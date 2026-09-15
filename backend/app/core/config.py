from pathlib import Path

from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    LLM_MODEL: str = "no_model"
    EMBEDDING_MODEL: str = "intfloat/multilingual-e5-base"
    COLLECTION_NAME: str = "collections_docs"
    QDRANT_URL: str = "http://localhost:6333"
    DATABASE_URL: str = "postgresql+asyncpg://rag:rag@localhost:5432/rag"
    REDIS_URL: str = "redis://localhost:6379"
    OPENROUTER_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    JWT_SECRET: str = "change-me"
    JWT_EXPIRE_MINUTES: int = 60
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    model_config = {"env_file": BASE_DIR.parent / ".env"}


settings = Settings()
