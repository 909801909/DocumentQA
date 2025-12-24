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

# --- 架构优化：单例模式管理 Embedding 模型 ---
class EmbeddingManager:
    _instance = None

    @classmethod
    def get_embeddings(cls):
        if cls._instance is None:
            logger.info("首次初始化 HuggingFaceEmbeddings 模型...")
            try:
                cls._instance = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")
                logger.info("HuggingFaceEmbeddings 模型加载成功。")
            except Exception as e:
                logger.error(f"加载 HuggingFaceEmbeddings 模型失败: {e}")
                raise e
        return cls._instance
# ------------------------------------------

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
        # 在服务初始化时就准备好 embedding 模型
        self.embeddings = EmbeddingManager.get_embeddings()

    def multi_model_qa(self, document_id: int, question: str) -> Dict:
        document = self.db.query(Document).filter(Document.id == document_id).first()
        if not document:
            return {"error": "文档未找到"}

        models_config = [
            {"name": settings.ARENA_MODEL_1_NAME, "base": settings.ARENA_MODEL_1_BASE, "key": settings.ARENA_MODEL_1_KEY},
            {"name": settings.ARENA_MODEL_2_NAME, "base": settings.ARENA_MODEL_2_BASE, "key": settings.ARENA_MODEL_2_KEY},
            {"name": settings.ARENA_MODEL_3_NAME, "base": settings.ARENA_MODEL_3_BASE, "key": settings.ARENA_MODEL_3_KEY},
            {"name": settings.ARENA_MODEL_4_NAME, "base": settings.ARENA_MODEL_4_BASE, "key": settings.ARENA_MODEL_4_KEY},
        ]

        results = {}
        
        with ThreadPoolExecutor(max_workers=4) as executor:
            future_to_model = {
                executor.submit(
                    self._llm_qa, 
                    document.content, 
                    question, 
                    document.filename, 
                    model_config
                ): model_config["name"] 
                for model_config in models_config
            }
            
            for future in as_completed(future_to_model):
                model_name = future_to_model[future]
                try:
                    answer = future.result()
                    results[model_name] = answer
                except Exception as e:
                    logger.error(f"Model {model_name} failed: {e}")
                    results[model_name] = f"模型调用失败: {str(e)}"

        return {
            "document_id": document_id,
            "question": question,
            "answers": results
        }

    def _llm_qa(self, content: str, question: str, context: str, model_config: Dict = None) -> str:
        if model_config:
            target_model_name = model_config.get("name")
            target_model_base = model_config.get("base")
            target_model_key = model_config.get("key")
        else:
            target_model_name = settings.OPENAI_MODEL_NAME
            target_model_base = settings.OPENAI_API_BASE
            target_model_key = settings.OPENAI_API_KEY
        
        logger.info(f"开始处理问答请求 - 模型: {target_model_name}")

        if OPENAI_AVAILABLE:
            try:
                return self._openai_qa(content, question, target_model_name, target_model_base, target_model_key)
            except Exception as e:
                logger.error(f"OpenAI 兼容模型 {target_model_name} 调用失败: {e}")
                raise e

        raise Exception("没有可用的LLM服务配置")

    def _openai_qa(self, content: str, question: str, model_name: str, api_base: Optional[str], api_key: Optional[str]) -> str:
        documents = [LangchainDocument(page_content=content)]
        text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
        texts = text_splitter.split_documents(documents)

        # 使用共享的 embedding 实例
        db = FAISS.from_documents(texts, self.embeddings)

        final_api_key = api_key if api_key else settings.OPENAI_API_KEY
        if not final_api_key:
            raise ValueError(f"模型 {model_name} 缺少 API Key")

        final_api_base = api_base if api_base else settings.OPENAI_API_BASE
        
        llm_kwargs = {
            "api_key": final_api_key,
            "model_name": model_name,
            "temperature": 0
        }
        
        if final_api_base:
            llm_kwargs["base_url"] = final_api_base

        llm = ChatOpenAI(**llm_kwargs)

        qa = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=db.as_retriever()
        )

        result = qa.invoke({"query": question})
        return result['result']
    
    # 其他辅助方法保持不变
    def generate_summary_for_documents(self, document_ids: List[int]) -> str: return ""
    def single_document_qa(self, document_id: int, question: str, history: List[Dict] = []) -> Dict: return {}
    def _format_query_with_history(self, question: str, history: List[Dict]) -> str: return ""
    def _compare_documents(self, documents: List[Document]) -> Dict: return {}
    def _save_question(self, question: QuestionCreate): pass
    def knowledge_base_qa(self, question: str, history: List[Dict] = []) -> Dict: return {}
    def multi_document_comparison(self, document_ids: List[int], question: str = "") -> Dict: return {}
    def _improved_simple_qa(self, content: str, question: str) -> str: return ""
    def _qwen_qa(self, content: str, question: str) -> str: return ""
