from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    PROJECT_NAME: str = "智能文档问答系统"
    PROJECT_VERSION: str = "1.0.0"
    PROJECT_DESCRIPTION: str = "一个智能文档问答系统，支持单文档问答、知识库问答、多文档对比、知识图谱构建、报告自动生成等功能"

    # Database
    DATABASE_URL: str = "sqlite:///./app.db"

    # API Keys & LLM Configuration
    # OpenAI 及兼容接口 (如 DeepSeek, Moonshot, Local LLM)
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_API_BASE: Optional[str] = None  # 新增: 支持自定义 API 地址
    # OPENAI_MODEL_NAME: str = "glm-4.5-air"  # 新增: 支持自定义模型名称
    OPENAI_MODEL_NAME: str = "glm-4-flash"  # 新增: 支持自定义模型名称

    # 通义千问
    QWEN_API_KEY: Optional[str] = None

    class Config:
        env_file = ".env"


settings = Settings()