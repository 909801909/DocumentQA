from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import List, Dict, Optional, Any

from app.services.qa_service import QAService
from app.core.database import get_db

router = APIRouter(prefix="/qa", tags=["question_answering"])


@router.post("/single-document")
async def single_document_qa(
        document_id: int,
        question: str,
        body: Dict[str, Any] = Body(default={}),  # 接收 history
        db: Session = Depends(get_db)
):
    history = body.get("history", [])
    qa_service = QAService(db)
    result = qa_service.single_document_qa(document_id, question, history)
    return result


@router.post("/knowledge-base")
async def knowledge_base_qa(
        question: str,
        body: Dict[str, Any] = Body(default={}),
        db: Session = Depends(get_db)
):
    history = body.get("history", [])
    qa_service = QAService(db)
    result = qa_service.knowledge_base_qa(question, history)
    return result


@router.post("/multi-document-comparison")
async def multi_document_comparison(
        payload: Dict[str, Any] = Body(...),
        db: Session = Depends(get_db)
):
    # 重构参数接收方式，支持 POST body
    document_ids = payload.get("document_ids", [])
    question = payload.get("question", "")

    qa_service = QAService(db)
    result = qa_service.multi_document_comparison(document_ids, question)
    return result