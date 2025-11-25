from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
import docx2txt
from pypdf import PdfReader
from io import BytesIO
import traceback
import logging

from app.services import document_service
from app.schemas.document import Document, DocumentCreate, DocumentResponse
from app.core.database import get_db

router = APIRouter(prefix="/documents", tags=["documents"], redirect_slashes=False)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@router.get("/", response_model=List[Document])
def read_documents(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    documents = document_service.get_documents(db, skip=skip, limit=limit)
    return documents


@router.get("/{document_id}", response_model=DocumentResponse)
def read_document(document_id: int, db: Session = Depends(get_db)):
    db_document = document_service.get_document(db, document_id=document_id)
    if db_document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return db_document


@router.post("/", response_model=DocumentResponse)
async def create_document(file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        logger.info(f"Uploading file: {file.filename}, content type: {file.content_type}")
        
        # 读取文件内容
        content = ""
        if file.content_type == "application/pdf":
            content = await extract_text_from_pdf(file)
        elif file.content_type in ["application/vnd.openxmlformats-officedocument.wordprocessingml.document", 
                                   "application/msword"]:
            content = await extract_text_from_docx(file)
        elif file.content_type == "text/plain":
            content = (await file.read()).decode('utf-8')
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {file.content_type}")
        
        logger.info(f"Extracted content length: {len(content)}")
        
        document_data = DocumentCreate(
            filename=file.filename,
            content=content
        )
        
        result = document_service.create_document(db, document=document_data)
        logger.info(f"Document created successfully with ID: {result.id}")
        return result
    except Exception as e:
        logger.error(f"Error uploading document: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}")


@router.delete("/{document_id}", response_model=DocumentResponse)
def delete_document(document_id: int, db: Session = Depends(get_db)):
    db_document = document_service.delete_document(db, document_id=document_id)
    if db_document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return db_document


async def extract_text_from_pdf(file: UploadFile):
    """从PDF文件中提取文本"""
    try:
        content = await file.read()
        logger.info(f"PDF file size: {len(content)} bytes")
        pdf_reader = PdfReader(BytesIO(content))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() or ""  # 处理None值
        return text
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error extracting text from PDF: {str(e)}")


async def extract_text_from_docx(file: UploadFile):
    """从DOCX文件中提取文本"""
    try:
        # 重新读取文件内容以确保文件指针位置正确
        content = await file.read()
        logger.info(f"DOCX file size: {len(content)} bytes")
        # 使用BytesIO创建新的文件对象
        file_obj = BytesIO(content)
        return docx2txt.process(file_obj)
    except Exception as e:
        logger.error(f"Error extracting text from DOCX: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error extracting text from DOCX: {str(e)}")