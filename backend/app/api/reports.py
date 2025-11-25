from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from typing import Dict
import json

from app.services.report_service import ReportService
from app.services.qa_service import QAService
from app.services.knowledge_graph_service import KnowledgeGraphService
from app.core.database import get_db

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("/generate")
async def generate_report(
    format: str = "pdf",
    title: str = "智能文档分析报告",
    db: Session = Depends(get_db)
):
    """
    自动生成分析报告
    
    Args:
        format: 报告格式 ('pdf' 或 'word')
        title: 报告标题
    """
    # 初始化服务
    report_service = ReportService()
    qa_service = QAService(db)
    kg_service = KnowledgeGraphService(db)
    
    # 构建报告内容
    report_content = {
        "title": title,
        "summary": "本报告基于文档库中的内容自动生成，涵盖了文档分析、问答和知识图谱等多个维度。",
        "sections": []
    }
    
    # 添加文档统计信息
    document_count = db.query(app.models.document.Document).count()
    report_content["sections"].append({
        "title": "文档概览",
        "content": f"文档库中共包含 {document_count} 份文档。"
    })
    
    # 添加知识图谱信息
    kg_data = kg_service.build_knowledge_graph()
    report_content["sections"].append({
        "title": "知识图谱分析",
        "content": f"从文档中提取出 {kg_data['node_count']} 个实体和 {kg_data['edge_count']} 个关系。"
    })
    
    # 添加图可视化（如果有）
    if kg_data["graph_image"]:
        report_content["graph_image"] = kg_data["graph_image"]
    
    try:
        # 生成报告
        report_data = report_service.generate_report(format, report_content)
        
        # 设置响应头
        media_type = "application/pdf" if format.lower() == "pdf" else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        filename = f"report.{format.lower()}"
        
        return Response(
            content=report_data,
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成报告时出错: {str(e)}")


from fastapi import Response
import app.models.document