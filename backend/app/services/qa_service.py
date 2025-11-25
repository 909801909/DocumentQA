from typing import List, Dict, Optional
from sqlalchemy.orm import Session
import re
import logging
from langchain.chains import RetrievalQA
from langchain.vectorstores import FAISS
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from langchain.docstore.document import Document as LangchainDocument

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
    """
    智能问答服务类
    提供单文档问答、知识库问答和多文档对比功能
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def single_document_qa(self, document_id: int, question: str) -> Dict:
        """
        单文档问答
        
        Args:
            document_id: 文档ID
            question: 问题
            
        Returns:
            包含答案和相关信息的字典
        """
        document = self.db.query(Document).filter(Document.id == document_id).first()
        if not document:
            return {"error": "文档未找到"}
        
        # 使用大语言模型进行问答
        answer = self._llm_qa(document.content, question, document.filename)
        
        # 保存问答记录
        question_obj = QuestionCreate(
            document_id=document_id,
            question=question,
            answer=answer
        )
        self._save_question(question_obj)
        
        return {
            "document_id": document_id,
            "document_title": document.filename,
            "question": question,
            "answer": answer
        }
    
    def knowledge_base_qa(self, question: str) -> Dict:
        """
        知识库问答（跨文档综合提问）
        
        Args:
            question: 问题
            
        Returns:
            包含答案和相关信息的字典
        """
        documents = self.db.query(Document).all()
        if not documents:
            return {"error": "文档库为空"}
        
        # 合并所有文档内容
        combined_content = "\n".join([doc.content for doc in documents])
        
        # 使用大语言模型进行问答
        answer = self._llm_qa(combined_content, question, "知识库")
        
        # 保存问答记录（不关联特定文档）
        question_obj = QuestionCreate(
            document_id=None,
            question=question,
            answer=answer
        )
        self._save_question(question_obj)
        
        return {
            "question": question,
            "answer": answer,
            "document_count": len(documents)
        }
    
    def multi_document_comparison(self, document_ids: List[int]) -> Dict:
        """
        多文档对比
        
        Args:
            document_ids: 文档ID列表
            
        Returns:
            包含对比分析结果的字典
        """
        if len(document_ids) < 2:
            return {"error": "至少需要两个文档进行对比"}
        
        documents = self.db.query(Document).filter(Document.id.in_(document_ids)).all()
        if len(documents) != len(document_ids):
            return {"error": "部分文档未找到"}
        
        # 简单的文档对比实现
        comparison_result = self._compare_documents(documents)
        
        return {
            "documents": [{"id": doc.id, "title": doc.filename} for doc in documents],
            "comparison": comparison_result
        }
    
    def _llm_qa(self, content: str, question: str, context: str) -> str:
        """
        使用大语言模型进行问答
        
        Args:
            content: 文档内容
            question: 用户问题
            context: 上下文信息
            
        Returns:
            模型回答
        """
        logger.info(f"开始处理问答请求 - OpenAI可用: {OPENAI_AVAILABLE}, Qwen可用: {QWEN_AVAILABLE}")
        logger.info(f"OpenAI API Key设置: {bool(settings.OPENAI_API_KEY)}")
        logger.info(f"Qwen API Key设置: {bool(settings.QWEN_API_KEY)}")
        
        # 如果配置了OpenAI API密钥且可以导入相关模块，则使用OpenAI
        if OPENAI_AVAILABLE and settings.OPENAI_API_KEY:
            try:
                logger.info("尝试使用OpenAI模型进行问答")
                result = self._openai_qa(content, question)
                logger.info("成功使用OpenAI模型进行问答")
                return result
            except Exception as e:
                logger.error(f"OpenAI调用失败: {e}")
                import traceback
                logger.error(f"OpenAI错误详情: {traceback.format_exc()}")
                # 如果OpenAI调用失败，尝试其他模型
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
                # 如果通义千问调用失败，回退到简单QA
                pass
        
        # 否则使用改进的简单QA逻辑
        logger.info("回退到简单QA逻辑")
        return self._improved_simple_qa(content, question)
    
    def _openai_qa(self, content: str, question: str) -> str:
        """
        使用OpenAI模型进行问答
        """
        # 创建Langchain文档对象
        documents = [LangchainDocument(page_content=content)]
        
        # 分割文本
        text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
        texts = text_splitter.split_documents(documents)
        
        # 创建嵌入和向量存储
        embeddings = HuggingFaceEmbeddings()
        db = FAISS.from_documents(texts, embeddings)
        
        # 创建OpenAI模型
        llm = ChatOpenAI(
            openai_api_key=settings.OPENAI_API_KEY,
            model_name="gpt-3.5-turbo",
            temperature=0
        )
        
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
        embeddings = HuggingFaceEmbeddings()
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
            # 对于询问主题的问题，返回文档的前几句话作为主题概述
            sentences = re.split(r'[.!?。！？]', content)
            # 过滤掉空句子
            sentences = [s.strip() for s in sentences if s.strip()]
            if sentences:
                # 返回前1-3句作为主题概述
                theme_sentences = sentences[:min(3, len(sentences))]
                return '。'.join(theme_sentences) + ('。' if theme_sentences else '')
        
        # 更智能的关键词匹配
        question_keywords = re.findall(r'\w+', question.lower())
        
        # 在内容中查找相关句子
        sentences = re.split(r'[.!?。！？]', content)
        relevant_sentences = []
        
        for sentence in sentences:
            sentence_lower = sentence.lower()
            match_count = sum(1 for kw in question_keywords if kw in sentence_lower)
            if match_count > 0:
                # 计算相关性得分，考虑句子长度和关键词密度
                score = match_count / len(sentence_lower.split()) if sentence_lower.split() else 0
                relevant_sentences.append((sentence, match_count, score))
        
        # 按匹配度和相关性排序
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
        
        # 获取所有文档的内容
        doc_contents = [doc.content for doc in documents]
        
        # 简单的长度比较
        lengths = [len(content) for content in doc_contents]
        result["length_comparison"] = {
            "document_lengths": lengths,
            "total_length": sum(lengths)
        }
        
        # 关键词提取（简化版）
        keywords_per_doc = []
        for content in doc_contents:
            words = re.findall(r'\b\w+\b', content.lower())
            # 统计词频
            word_freq = {}
            for word in words:
                word_freq[word] = word_freq.get(word, 0) + 1
            # 获取高频词
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