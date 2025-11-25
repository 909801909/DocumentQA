from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    PROJECT_NAME: str = "智能文档问答系统"
    PROJECT_VERSION: str = "1.0.0"
    PROJECT_DESCRIPTION: str = "一个智能文档问答系统，支持单文档问答、知识库问答、多文档对比、知识图谱构建、报告自动生成等功能"

    # Database
    DATABASE_URL: str = "sqlite:///./app.db"

    # API Keys (如果需要的话)
    OPENAI_API_KEY: Optional[str] = None
    QWEN_API_KEY: Optional[str] = None

    class Config:
        env_file = ".env"


settings = Settings()