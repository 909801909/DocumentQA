from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class QuestionBase(BaseModel):
    document_id: Optional[int] = None
    question: str
    answer: str


class QuestionCreate(QuestionBase):
    pass


class QuestionUpdate(QuestionBase):
    pass


class QuestionInDBBase(QuestionBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class Question(QuestionInDBBase):
    pass


class QuestionResponse(QuestionInDBBase):
    pass