from sqlalchemy.orm import Session
from app.models.question import Question
from app.schemas.question import QuestionCreate, QuestionUpdate


def get_question(db: Session, question_id: int):
    return db.query(Question).filter(Question.id == question_id).first()


def get_questions(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Question).offset(skip).limit(limit).all()


def create_question(db: Session, question: QuestionCreate):
    db_question = Question(
        document_id=question.document_id,
        question=question.question,
        answer=question.answer
    )
    db.add(db_question)
    db.commit()
    db.refresh(db_question)
    return db_question


def update_question(db: Session, question_id: int, question: QuestionUpdate):
    db_question = db.query(Question).filter(Question.id == question_id).first()
    if db_question:
        db_question.document_id = question.document_id
        db_question.question = question.question
        db_question.answer = question.answer
        db.commit()
        db.refresh(db_question)
    return db_question


def delete_question(db: Session, question_id: int):
    db_question = db.query(Question).filter(Question.id == question_id).first()
    if db_question:
        db.delete(db_question)
        db.commit()
    return db_question