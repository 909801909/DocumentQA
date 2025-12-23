import os
# --- 关键修改：设置 Hugging Face 国内镜像 ---
# 这行代码必须在导入 langchain 或 transformers 之前执行
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
# ------------------------------------------

from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session
import re
import logging
from langchain.chains import RetrievalQA
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from langchain_core.documents import Document as LangchainDocument

from app.models.document import Document
from app.models.question import Question
from app.schemas.question import QuestionCreate
from app.core.config import settings

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 条件导入不同平台的模块
try:
    from langchain_openai import ChatOpenAI

    OPENAI_AVAILABLE = True
    logger.info("OpenAI模块导入成功")
except ImportError as e:
    OPENAI_AVAILABLE = False
    ChatOpenAI = None
    logger.info(f"OpenAI模块导入失败: {e}")

try:
    from langchain_community.llms import Tongyi

    QWEN_AVAILABLE = True
    logger.info("通义千问(Tongyi)模块导入成功")
except ImportError as e:
    QWEN_AVAILABLE = False
    Tongyi = None
    logger.info(f"通义千问(Tongyi)模块导入失败: {e}")


class QAService:
    def __init__(self, db: Session):
        self.db = db

    def generate_summary_for_documents(self, document_ids: List[int]) -> str:
        """
        为指定的多个文档生成一个综合性的摘要。
        """
        if not document_ids:
            return "没有选择任何文档以生成摘要。"

        documents = self.db.query(Document).filter(Document.id.in_(document_ids)).all()
        if not documents:
            return "所选文档未找到。"

        # 合并所有文档内容，并为每个文档内容添加标题以作区分
        combined_content = "\n\n".join(
            [f"--- 文档: {doc.filename} ---\n{doc.content}" for doc in documents]
        )

        # 创建一个专门用于生成摘要的prompt
        summary_prompt = (
            "请根据以下提供的全部内容，生成一段综合性的、流畅的摘要。"
            "摘要应涵盖所有文档的核心要点，并以一个段落的形式呈现。"
            "请直接输出摘要内容，不要包含任何额外的引导性文字，如“这是摘要：”。"
        )

        # 使用现有的LLM问答逻辑来生成摘要
        # 我们将合并后的内容作为“上下文”，将摘要prompt作为“问题”
        summary = self._llm_qa(combined_content, summary_prompt, "文档摘要生成")
        
        return summary

    def single_document_qa(self, document_id: int, question: str, history: List[Dict] = []) -> Dict:
        document = self.db.query(Document).filter(Document.id == document_id).first()
        if not document:
            return {"error": "文档未找到"}

        # 构建包含历史的上下文 Query
        full_query = self._format_query_with_history(question, history)

        answer = self._llm_qa(document.content, full_query, document.filename)

        # 保存记录 (可选：保存带历史的上下文或仅保存当前问题)
        self._save_question(QuestionCreate(
            document_id=document_id,
            question=question,
            answer=answer
        ))

        return {
            "document_id": document_id,
            "document_title": document.filename,
            "question": question,
            "answer": answer
        }

    def knowledge_base_qa(self, question: str, history: List[Dict] = []) -> Dict:
        documents = self.db.query(Document).all()
        if not documents:
            return {"error": "文档库为空"}

        # 优化：给每个文档内容加上标题前缀，帮助 LLM 区分来源
        combined_content_parts = []
        for doc in documents:
            combined_content_parts.append(
                f"--- 文档: {doc.filename} ---\n{doc.content[:2000]}...")  # 截断以防止 Token 溢出，实际生产应使用向量库检索

        combined_content = "\n\n".join(combined_content_parts)
        full_query = self._format_query_with_history(question, history)

        answer = self._llm_qa(combined_content, full_query, "知识库全部文档")

        self._save_question(QuestionCreate(
            document_id=None,
            question=question,
            answer=answer
        ))

        return {
            "question": question,
            "answer": answer,
            "document_count": len(documents)
        }

    def multi_document_comparison(self, document_ids: List[int], question: str = "") -> Dict:
        if len(document_ids) < 2:
            return {"error": "至少需要两个文档进行对比"}

        documents = self.db.query(Document).filter(Document.id.in_(document_ids)).all()

        # 基础统计对比
        base_comparison = self._compare_documents(documents)

        # 智能 LLM 对比分析
        docs_text = "\n\n".join([f"文档 [{doc.filename}]:\n{doc.content[:1500]}" for doc in documents])
        prompt = f"请对比以下几篇文档的内容。{question if question else '分析它们的主要观点、数据差异和共同点。'} 请以 Markdown 格式输出详细的对比报告。\n\n{docs_text}"

        ai_analysis = self._llm_qa(docs_text, prompt, "多文档对比")

        return {
            "documents": [{"id": doc.id, "title": doc.filename} for doc in documents],
            "comparison": base_comparison,
            "ai_analysis": ai_analysis
        }

    def _format_query_with_history(self, question: str, history: List[Dict]) -> str:
        """
        格式化包含历史记录的问题
        """
        if not history:
            return question

        history_text = ""
        for msg in history:
            role = "用户" if msg['role'] == 'user' else "助手"
            history_text += f"{role}: {msg['content']}\n"

        return f"以下是历史对话：\n{history_text}\n现在用户的问题是：{question}\n请根据上下文回答。"

    def _llm_qa(self, content: str, question: str, context: str) -> str:
        """
        使用大语言模型进行问答
        """
        logger.info(f"开始处理问答请求 - OpenAI可用: {OPENAI_AVAILABLE}, Qwen可用: {QWEN_AVAILABLE}")

        # 如果配置了OpenAI API密钥且可以导入相关模块，则使用OpenAI (或兼容接口)
        if OPENAI_AVAILABLE and settings.OPENAI_API_KEY:
            try:
                model_name = settings.OPENAI_MODEL_NAME
                logger.info(f"尝试使用OpenAI兼容模型进行问答, 模型: {model_name}")
                result = self._openai_qa(content, question)
                logger.info("成功使用OpenAI兼容模型进行问答")
                return result
            except Exception as e:
                logger.error(f"OpenAI调用失败: {e}")
                import traceback
                logger.error(f"OpenAI错误详情: {traceback.format_exc()}")
                # 如果调用失败，尝试其他模型或回退
                pass

        # 如果配置了通义千问API密钥，则使用通义千问
        if QWEN_AVAILABLE and settings.QWEN_API_KEY:
            try:
                logger.info("尝试使用通义千问模型进行问答")
                result = self._qwen_qa(content, question)
                logger.info("成功使用通义千问模型进行问答")
                return result
            except Exception as e:
                logger.error(f"通义千问调用失败: {e}")
                import traceback
                logger.error(f"通义千问错误详情: {traceback.format_exc()}")
                pass

        # 否则使用改进的简单QA逻辑
        logger.info("回退到简单QA逻辑")
        return self._improved_simple_qa(content, question)

    def _openai_qa(self, content: str, question: str) -> str:
        """
        使用OpenAI或兼容模型进行问答
        """
        # 创建Langchain文档对象
        documents = [LangchainDocument(page_content=content)]

        # 分割文本
        text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
        texts = text_splitter.split_documents(documents)

        # 创建嵌入和向量存储
        # 显式指定 model_name 以消除警告
        embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")
        db = FAISS.from_documents(texts, embeddings)

        # 准备模型参数
        llm_kwargs = {
            "openai_api_key": settings.OPENAI_API_KEY,
            "model_name": settings.OPENAI_MODEL_NAME,  # 使用配置的模型名称
            "temperature": 0
        }

        # 如果设置了自定义Base URL (例如用于DeepSeek, LocalAI等)
        if settings.OPENAI_API_BASE:
            llm_kwargs["openai_api_base"] = settings.OPENAI_API_BASE

        # 创建OpenAI模型
        llm = ChatOpenAI(**llm_kwargs)

        # 创建问答链
        qa = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=db.as_retriever()
        )

        # 提出问题
        result = qa.invoke({"query": question})
        return result['result']

    def _qwen_qa(self, content: str, question: str) -> str:
        """
        使用通义千问模型进行问答
        """
        logger.info(f"开始调用通义千问模型，API Key是否存在: {bool(settings.QWEN_API_KEY)}")

        # 创建Langchain文档对象
        documents = [LangchainDocument(page_content=content)]

        # 分割文本
        text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
        texts = text_splitter.split_documents(documents)

        # 创建嵌入和向量存储
        # 显式指定 model_name 以消除警告
        embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")
        db = FAISS.from_documents(texts, embeddings)

        # 创建通义千问模型
        llm = Tongyi(
            model_name="qwen-turbo",
            dashscope_api_key=settings.QWEN_API_KEY,
            top_p=0.8,
            temperature=0.7
        )

        # 创建问答链
        qa = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=db.as_retriever()
        )

        # 提出问题
        logger.info("正在向通义千问模型提问...")
        result = qa.invoke({"query": question})
        logger.info("通义千问模型返回结果")
        return result['result']

    def _improved_simple_qa(self, content: str, question: str) -> str:
        """
        改进的简单问答实现
        """
        # 特殊问题处理
        if any(keyword in question.lower() for keyword in ['主题', '主旨', '主要', '中心']):
            sentences = re.split(r'[.!?。！？]', content)
            sentences = [s.strip() for s in sentences if s.strip()]
            if sentences:
                theme_sentences = sentences[:min(3, len(sentences))]
                return '。'.join(theme_sentences) + ('。' if theme_sentences else '')

        # 更智能的关键词匹配
        question_keywords = re.findall(r'\w+', question.lower())
        sentences = re.split(r'[.!?。！？]', content)
        relevant_sentences = []

        for sentence in sentences:
            sentence_lower = sentence.lower()
            match_count = sum(1 for kw in question_keywords if kw in sentence_lower)
            if match_count > 0:
                score = match_count / len(sentence_lower.split()) if sentence_lower.split() else 0
                relevant_sentences.append((sentence, match_count, score))

        relevant_sentences.sort(key=lambda x: (x[1], x[2]), reverse=True)

        if relevant_sentences:
            return relevant_sentences[0][0].strip()
        else:
            return "根据现有文档内容无法找到确切答案。"

    def _compare_documents(self, documents: List[Document]) -> Dict:
        """
        简单的文档对比实现
        """
        result = {
            "similarities": [],
            "differences": []
        }
        doc_contents = [doc.content for doc in documents]
        lengths = [len(content) for content in doc_contents]
        result["length_comparison"] = {
            "document_lengths": lengths,
            "total_length": sum(lengths)
        }
        keywords_per_doc = []
        for content in doc_contents:
            words = re.findall(r'\b\w+\b', content.lower())
            word_freq = {}
            for word in words:
                word_freq[word] = word_freq.get(word, 0) + 1
            sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
            top_words = [word for word, freq in sorted_words[:10]]
            keywords_per_doc.append(top_words)
        result["top_keywords"] = keywords_per_doc
        return result

    def _save_question(self, question: QuestionCreate):
        """
        保存问题到数据库
        """
        db_question = Question(
            document_id=question.document_id,
            question=question.question,
            answer=question.answer
        )
        self.db.add(db_question)
        self.db.commit()
        self.db.refresh(db_question)