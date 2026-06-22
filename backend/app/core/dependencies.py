from functools import lru_cache

from app.db.vector_store import VectorStore
from app.services.llm import LLMAssistant


@lru_cache
def get_vector_store() -> VectorStore:
    return VectorStore()


@lru_cache
def get_llm() -> LLMAssistant:
    return LLMAssistant()
