from pydantic import BaseModel
from datetime import datetime


class UsageStatsBase(BaseModel):
    user_id: str
    feature: str


class UsageStatsCreate(UsageStatsBase):
    pass


class UsageStatsInDBBase(UsageStatsBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class UsageStats(UsageStatsInDBBase):
    pass