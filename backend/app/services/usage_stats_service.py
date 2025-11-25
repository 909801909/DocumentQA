from sqlalchemy.orm import Session
from app.models.usage_stats import UsageStats
from app.schemas.usage_stats import UsageStatsCreate


def get_usage_stat(db: Session, usage_stat_id: int):
    return db.query(UsageStats).filter(UsageStats.id == usage_stat_id).first()


def get_usage_stats(db: Session, skip: int = 0, limit: int = 100):
    return db.query(UsageStats).offset(skip).limit(limit).all()


def create_usage_stat(db: Session, usage_stat: UsageStatsCreate):
    db_usage_stat = UsageStats(
        user_id=usage_stat.user_id,
        feature=usage_stat.feature
    )
    db.add(db_usage_stat)
    db.commit()
    db.refresh(db_usage_stat)
    return db_usage_stat