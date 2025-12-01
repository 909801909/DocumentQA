from fastapi import APIRouter, Depends, HTTPException, Response, Body
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
import urllib.parse

from app.services.report_service import ReportService
from app.services.knowledge_graph_service import KnowledgeGraphService
from app.services.qa_service import QAService  # 导入 QAService
from app.core.database import get_db
from app.models.document import Document

router = APIRouter(prefix="/reports", tags=["reports"])

@router.post("/generate")
async def generate_report(
    format: str = Body("pdf", embed=True),
    title: str = Body("智能文档分析报告", embed=True),
    document_ids: List[int] = Body(..., embed=True),
    db: Session = Depends(get_db)
):
    """
    自动生成分析报告
    """
    if not document_ids:
        raise HTTPException(status_code=400, detail="请至少选择一个文档")

    # 初始化所有需要的服务
    report_service = ReportService()
    kg_service = KnowledgeGraphService(db)
    qa_service = QAService(db)  # 实例化 QAService
    
    selected_docs = db.query(Document).filter(Document.id.in_(document_ids)).all()
    if not selected_docs:
        raise HTTPException(status_code=404, detail="所选文档未找到")

    # --- 生成动态摘要 ---
    summary_text = qa_service.generate_summary_for_documents(document_ids)

    # 构建报告内容，使用动态生成的摘要
    report_content = {
        "title": title,
        "summary": summary_text
    }
    
    # 为选定的所有文档构建一个统一的知识图谱
    for doc_id in document_ids:
        kg_service.build_knowledge_graph(doc_id)

    kg_image_base64 = kg_service.generate_graph_image_base64()
    
    try:
        report_data = report_service.generate_report(
            format=format,
            content=report_content,
            selected_docs=[{"filename": doc.filename} for doc in selected_docs],
            kg_image_base64=kg_image_base64
        )
        
        media_type = "application/pdf" if format.lower() == "pdf" else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        
        encoded_filename = urllib.parse.quote(f"{title.replace(' ', '_')}.{format.lower()}")
        fallback_filename = f"report.{format.lower()}"
        
        disposition = f"attachment; filename=\"{fallback_filename}\"; filename*=UTF-8''{encoded_filename}"
        
        return Response(
            content=report_data,
            media_type=media_type,
            headers={"Content-Disposition": disposition}
        )
    except Exception as e:
        print(f"Error generating report: {e}")
        raise HTTPException(status_code=500, detail=f"生成报告时出错: {str(e)}")
