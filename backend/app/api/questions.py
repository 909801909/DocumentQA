from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.services import question_service
from app.schemas.question import Question, QuestionCreate, QuestionResponse
from app.core.database import get_db

router = APIRouter(prefix="/questions", tags=["questions"])


@router.get("/", response_model=List[Question])
def read_questions(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    questions = question_service.get_questions(db, skip=skip, limit=limit)
    return questions


@router.get("/{question_id}", response_model=QuestionResponse)
def read_question(question_id: int, db: Session = Depends(get_db)):
    db_question = question_service.get_question(db, question_id=question_id)
    if db_question is None:
        raise HTTPException(status_code=404, detail="Question not found")
    return db_question


@router.post("/", response_model=QuestionResponse)
def create_question(question: QuestionCreate, db: Session = Depends(get_db)):
    return question_service.create_question(db, question=question)


@router.delete("/{question_id}", response_model=QuestionResponse)
def delete_question(question_id: int, db: Session = Depends(get_db)):
    db_question = question_service.delete_question(db, question_id=question_id)
    if db_question is None:
        raise HTTPException(status_code=404, detail="Question not found")
    return db_question