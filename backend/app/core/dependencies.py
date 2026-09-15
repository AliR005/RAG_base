from functools import lru_cache

from app.adapters.embeddings.bge_m3 import BgeM3EmbeddingProvider
from app.adapters.llm.factory import LLMProviderFactory
from app.adapters.reranker.bge_reranker import BgeReranker
from app.adapters.vector_store.qdrant_store import QdrantVectorStore
from app.application.retrieve import RetrieveUseCase
from app.core.config import settings
from app.db.vector_store import VectorStore
from app.services.llm import LLMAssistant


@lru_cache
def get_vector_store() -> VectorStore:
    return VectorStore()


@lru_cache
def get_llm() -> LLMAssistant:
    return LLMAssistant()


@lru_cache
def get_embedding_provider() -> BgeM3EmbeddingProvider:
    return BgeM3EmbeddingProvider(settings.EMBEDDING_MODEL)


@lru_cache
def get_qdrant_store() -> QdrantVectorStore:
    return QdrantVectorStore(
        url=settings.QDRANT_URL, collection=settings.COLLECTION_NAME
    )


@lru_cache
def get_reranker() -> BgeReranker:
    return BgeReranker()


@lru_cache
def get_llm_factory() -> LLMProviderFactory:
    return LLMProviderFactory(
        openrouter_key=settings.OPENROUTER_API_KEY,
        anthropic_key=settings.ANTHROPIC_API_KEY,
        ollama_model=settings.LLM_MODEL,
    )


@lru_cache
def get_retrieve_usecase() -> RetrieveUseCase:
    return RetrieveUseCase(
        vectors=get_qdrant_store(),
        embeddings=get_embedding_provider(),
        reranker=get_reranker(),
    )
