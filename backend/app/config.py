import os

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))


class Settings:
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 8000))
    GLOBAL_URL = os.getenv("GLOBAL_URL", "")
    EMBEDDING_MODEL = "intfloat/multilingual-e5-base"
    LLM_MODEL = os.getenv("MODELNAME", "no_model")
    CHROMA_PATH = os.getenv("CHROMA_PATH", "../chroma_db")
    COLLECTION_NAME = "collections_docs"
    API_KEY_MODEL = os.getenv("API_MODELS", "default")


settings = Settings()
