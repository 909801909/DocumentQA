from sqlalchemy import Column, Integer, String, DateTime, func
from app.core.database import Base


class UsageStats(Base):
    __tablename__ = "usage_stats"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    feature = Column(String)  # 使用的功能
    created_at = Column(DateTime, default=func.now())