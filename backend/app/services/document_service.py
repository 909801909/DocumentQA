from sqlalchemy.orm import Session
from app.models.document import Document
from app.schemas.document import DocumentCreate, DocumentUpdate


def get_document(db: Session, document_id: int):
    return db.query(Document).filter(Document.id == document_id).first()


def get_documents(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Document).offset(skip).limit(limit).all()


def create_document(db: Session, document: DocumentCreate):
    db_document = Document(filename=document.filename, content=document.content)
    db.add(db_document)
    db.commit()
    db.refresh(db_document)
    return db_document


def update_document(db: Session, document_id: int, document: DocumentUpdate):
    db_document = db.query(Document).filter(Document.id == document_id).first()
    if db_document:
        db_document.filename = document.filename
        db_document.content = document.content
        db.commit()
        db.refresh(db_document)
    return db_document


def delete_document(db: Session, document_id: int):
    db_document = db.query(Document).filter(Document.id == document_id).first()
    if db_document:
        db.delete(db_document)
        db.commit()
    return db_document