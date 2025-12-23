import os
# --- 关键修改：设置 Hugging Face 国内镜像 ---
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
# ------------------------------------------

from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session
import re
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
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

    def multi_model_qa(self, document_id: int, question: str) -> Dict:
        """
        使用4个不同的模型同时回答同一个问题
        """
        document = self.db.query(Document).filter(Document.id == document_id).first()
        if not document:
            return {"error": "文档未找到"}

        models = [
            settings.ARENA_MODEL_1,
            settings.ARENA_MODEL_2,
            settings.ARENA_MODEL_3,
            settings.ARENA_MODEL_4
        ]

        results = {}
        
        # 使用线程池并发调用4个模型
        with ThreadPoolExecutor(max_workers=4) as executor:
            future_to_model = {
                executor.submit(self._llm_qa, document.content, question, document.filename, model_name): model_name 
                for model_name in models
            }
            
            for future in as_completed(future_to_model):
                model_name = future_to_model[future]
                try:
                    answer = future.result()
                    results[model_name] = answer
                except Exception as e:
                    logger.error(f"Model {model_name} failed: {e}")
                    results[model_name] = f"Error: {str(e)}"

        return {
            "document_id": document_id,
            "question": question,
            "answers": results
        }

    def generate_summary_for_documents(self, document_ids: List[int]) -> str:
        if not document_ids:
            return "没有选择任何文档以生成摘要。"

        documents = self.db.query(Document).filter(Document.id.in_(document_ids)).all()
        if not documents:
            return "所选文档未找到。"

        combined_content = "\n\n".join(
            [f"--- 文档: {doc.filename} ---\n{doc.content}" for doc in documents]
        )

        summary_prompt = (
            "请根据以下提供的全部内容，生成一段综合性的、流畅的摘要。"
            "摘要应涵盖所有文档的核心要点，并以一个段落的形式呈现。"
            "请直接输出摘要内容，不要包含任何额外的引导性文字，如“这是摘要：”。"
        )

        summary = self._llm_qa(combined_content, summary_prompt, "文档摘要生成")
        return summary

    def single_document_qa(self, document_id: int, question: str, history: List[Dict] = []) -> Dict:
        document = self.db.query(Document).filter(Document.id == document_id).first()
        if not document:
            return {"error": "文档未找到"}

        full_query = self._format_query_with_history(question, history)
        answer = self._llm_qa(document.content, full_query, document.filename)

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

        combined_content_parts = []
        for doc in documents:
            combined_content_parts.append(
                f"--- 文档: {doc.filename} ---\n{doc.content[:2000]}...")

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
        base_comparison = self._compare_documents(documents)

        docs_text = "\n\n".join([f"文档 [{doc.filename}]:\n{doc.content[:1500]}" for doc in documents])
        prompt = f"请对比以下几篇文档的内容。{question if question else '分析它们的主要观点、数据差异和共同点。'} 请以 Markdown 格式输出详细的对比报告。\n\n{docs_text}"

        ai_analysis = self._llm_qa(docs_text, prompt, "多文档对比")

        return {
            "documents": [{"id": doc.id, "title": doc.filename} for doc in documents],
            "comparison": base_comparison,
            "ai_analysis": ai_analysis
        }

    def _format_query_with_history(self, question: str, history: List[Dict]) -> str:
        if not history:
            return question
        history_text = ""
        for msg in history:
            role = "用户" if msg['role'] == 'user' else "助手"
            history_text += f"{role}: {msg['content']}\n"
        return f"以下是历史对话：\n{history_text}\n现在用户的问题是：{question}\n请根据上下文回答。"

    def _llm_qa(self, content: str, question: str, context: str, model_name: str = None) -> str:
        """
        使用大语言模型进行问答。支持指定 model_name。
        """
        # 如果没有指定 model_name，使用默认配置
        target_model = model_name if model_name else settings.OPENAI_MODEL_NAME
        
        logger.info(f"开始处理问答请求 - 模型: {target_model}")

        if OPENAI_AVAILABLE and settings.OPENAI_API_KEY:
            try:
                return self._openai_qa(content, question, target_model)
            except Exception as e:
                logger.error(f"OpenAI调用失败: {e}")
                pass

        if QWEN_AVAILABLE and settings.QWEN_API_KEY:
            try:
                return self._qwen_qa(content, question)
            except Exception as e:
                logger.error(f"通义千问调用失败: {e}")
                pass

        logger.info("回退到简单QA逻辑")
        return self._improved_simple_qa(content, question)

    def _openai_qa(self, content: str, question: str, model_name: str) -> str:
        documents = [LangchainDocument(page_content=content)]
        text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
        texts = text_splitter.split_documents(documents)

        embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")
        db = FAISS.from_documents(texts, embeddings)

        llm_kwargs = {
            "openai_api_key": settings.OPENAI_API_KEY,
            "model_name": model_name,
            "temperature": 0
        }

        if settings.OPENAI_API_BASE:
            llm_kwargs["openai_api_base"] = settings.OPENAI_API_BASE

        llm = ChatOpenAI(**llm_kwargs)

        qa = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=db.as_retriever()
        )

        result = qa.invoke({"query": question})
        return result['result']

    def _qwen_qa(self, content: str, question: str) -> str:
        # Qwen 的实现暂时不支持动态切换模型名称，仍使用默认配置
        # 如果需要支持，可以类似 _openai_qa 进行修改
        logger.info(f"开始调用通义千问模型")
        documents = [LangchainDocument(page_content=content)]
        text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
        texts = text_splitter.split_documents(documents)
        embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")
        db = FAISS.from_documents(texts, embeddings)
        llm = Tongyi(
            model_name="qwen-turbo",
            dashscope_api_key=settings.QWEN_API_KEY,
            top_p=0.8,
            temperature=0.7
        )
        qa = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=db.as_retriever()
        )
        result = qa.invoke({"query": question})
        return result['result']

    def _improved_simple_qa(self, content: str, question: str) -> str:
        if any(keyword in question.lower() for keyword in ['主题', '主旨', '主要', '中心']):
            sentences = re.split(r'[.!?。！？]', content)
            sentences = [s.strip() for s in sentences if s.strip()]
            if sentences:
                theme_sentences = sentences[:min(3, len(sentences))]
                return '。'.join(theme_sentences) + ('。' if theme_sentences else '')

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
        db_question = Question(
            document_id=question.document_id,
            question=question.question,
            answer=question.answer
        )
        self.db.add(db_question)
        self.db.commit()
        self.db.refresh(db_question)