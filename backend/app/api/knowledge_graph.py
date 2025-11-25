from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.services.knowledge_graph_service import KnowledgeGraphService
from app.core.database import get_db

router = APIRouter(prefix="/knowledge-graph", tags=["knowledge_graph"])


@router.post("/build")
async def build_knowledge_graph(db: Session = Depends(get_db)):
    """
    构建知识图谱
    
    Returns:
        包含节点、边和图可视化信息的字典
    """
    kg_service = KnowledgeGraphService(db)
    result = kg_service.build_knowledge_graph()
    return result


@router.get("/visualize")
async def visualize_knowledge_graph(db: Session = Depends(get_db)):
    """
    获取知识图谱的可视化图像
    
    Returns:
        base64编码的图像字符串
    """
    kg_service = KnowledgeGraphService(db)
    result = kg_service.build_knowledge_graph()
    return {"graph_image": result["graph_image"]}