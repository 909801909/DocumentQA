from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.services.qa_service import QAService
from app.core.database import get_db

router = APIRouter(prefix="/qa", tags=["question_answering"])


@router.post("/single-document")
async def single_document_qa(document_id: int, question: str, db: Session = Depends(get_db)):
    """
    单文档问答
    
    Args:
        document_id: 文档ID
        question: 问题
    """
    qa_service = QAService(db)
    result = qa_service.single_document_qa(document_id, question)
    return result


@router.post("/knowledge-base")
async def knowledge_base_qa(question: str, db: Session = Depends(get_db)):
    """
    知识库问答（跨文档综合提问）
    
    Args:
        question: 问题
    """
    qa_service = QAService(db)
    result = qa_service.knowledge_base_qa(question)
    return result


@router.post("/multi-document-comparison")
async def multi_document_comparison(document_ids: List[int], db: Session = Depends(get_db)):
    """
    多文档对比
    
    Args:
        document_ids: 文档ID列表
    """
    qa_service = QAService(db)
    result = qa_service.multi_document_comparison(document_ids)
    return result