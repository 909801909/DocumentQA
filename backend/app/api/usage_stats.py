from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List

from app.services import usage_stats_service
from app.schemas.usage_stats import UsageStats, UsageStatsCreate
from app.core.database import get_db

router = APIRouter(prefix="/usage-stats", tags=["usage_stats"])


@router.get("/", response_model=List[UsageStats])
def read_usage_stats(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    usage_stats = usage_stats_service.get_usage_stats(db, skip=skip, limit=limit)
    return usage_stats


@router.post("/", response_model=UsageStats)
def create_usage_stat(usage_stat: UsageStatsCreate, db: Session = Depends(get_db)):
    return usage_stats_service.create_usage_stat(db, usage_stat=usage_stat)


@router.post("/track-feature")
async def track_feature(feature: str, request: Request, db: Session = Depends(get_db)):
    # 获取用户ID（示例中使用IP地址作为用户标识）
    user_id = request.client.host
    
    # 创建使用统计记录
    usage_stat = UsageStatsCreate(user_id=user_id, feature=feature)
    result = usage_stats_service.create_usage_stat(db, usage_stat=usage_stat)
    
    return {"message": "Feature usage tracked successfully", "data": result}


@router.get("/statistics")
def get_statistics(db: Session = Depends(get_db)):
    stats = usage_stats_service.get_usage_stats(db)
    # 按功能分组统计
    feature_stats = {}
    for stat in stats:
        if stat.feature not in feature_stats:
            feature_stats[stat.feature] = 0
        feature_stats[stat.feature] += 1
    
    return feature_stats