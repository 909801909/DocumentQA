from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    PROJECT_NAME: str = "智能文档问答系统"
    PROJECT_VERSION: str = "1.0.0"
    PROJECT_DESCRIPTION: str = "一个智能文档问答系统，支持单文档问答、知识库问答、多文档对比、知识图谱构建、报告自动生成等功能"

    # Database
    DATABASE_URL: str = "sqlite:///./app.db"

    # API Keys & LLM Configuration
    # 默认单模型配置 (OpenAI 兼容)
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_API_BASE: Optional[str] = None
    OPENAI_MODEL_NAME: str = "glm-4-flash"

    # --- 多模型竞技场配置 (支持不同厂商) ---
    # 模型 1
    ARENA_MODEL_1_NAME: str = "glm-4-flash"
    ARENA_MODEL_1_BASE: Optional[str] = None
    ARENA_MODEL_1_KEY: Optional[str] = None

    # 模型 2
    ARENA_MODEL_2_NAME: str = "glm-4-air"
    ARENA_MODEL_2_BASE: Optional[str] = None
    ARENA_MODEL_2_KEY: Optional[str] = None

    # 模型 3
    ARENA_MODEL_3_NAME: str = "glm-4"
    ARENA_MODEL_3_BASE: Optional[str] = None
    ARENA_MODEL_3_KEY: Optional[str] = None

    # 模型 4
    ARENA_MODEL_4_NAME: str = "glm-3-turbo"
    ARENA_MODEL_4_BASE: Optional[str] = None
    ARENA_MODEL_4_KEY: Optional[str] = None
    # -----------------------

    # 通义千问 (旧版原生SDK配置，建议优先使用 OpenAI 兼容配置)
    QWEN_API_KEY: Optional[str] = None

    class Config:
        env_file = ".env"


settings = Settings()