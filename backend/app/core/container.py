"""Composition root: сборка всех зависимостей в одном месте.

Роутеры получают готовые use-case'ы/репозитории через Depends,
а не через разбросанные lru_cache-синглтоны.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.adapters.chunkers.hybrid_chunker import HybridChunker
from app.adapters.db.postgres import (
    PostgresChatRepository,
    PostgresDocumentRepository,
    PostgresUserRepository,
    make_session_factory,
)
from app.adapters.embeddings.bge_m3 import BgeM3EmbeddingProvider
from app.adapters.llm.factory import LLMProviderFactory
from app.adapters.loaders.factory import LoaderFactory
from app.adapters.reranker.bge_reranker import BgeReranker
from app.adapters.vector_store.qdrant_store import QdrantVectorStore
from app.application.ingest import IngestDocumentUseCase
from app.application.retrieve import RetrieveUseCase
from app.core.config import Settings


@dataclass
class AppContainer:
    users: PostgresUserRepository
    chats: PostgresChatRepository
    documents: PostgresDocumentRepository
    vectors: QdrantVectorStore
    embeddings: BgeM3EmbeddingProvider
    reranker: BgeReranker
    llm_factory: LLMProviderFactory
    chunker: HybridChunker
    loaders: LoaderFactory

    def retrieve(self) -> RetrieveUseCase:
        return RetrieveUseCase(
            vectors=self.vectors,
            embeddings=self.embeddings,
            reranker=self.reranker,
        )

    def ingest(self) -> IngestDocumentUseCase:
        return IngestDocumentUseCase(
            documents=self.documents,
            vectors=self.vectors,
            embeddings=self.embeddings,
            chunker=self.chunker,
            factory=self.loaders,
        )


def build_container(settings: Settings) -> AppContainer:
    sessions = make_session_factory(settings.DATABASE_URL)
    return AppContainer(
        users=PostgresUserRepository(sessions),
        chats=PostgresChatRepository(sessions),
        documents=PostgresDocumentRepository(sessions),
        vectors=QdrantVectorStore(
            url=settings.QDRANT_URL,
            collection=settings.COLLECTION_NAME,
        ),
        embeddings=BgeM3EmbeddingProvider(settings.EMBEDDING_MODEL),
        reranker=BgeReranker(),
        llm_factory=LLMProviderFactory(
            openrouter_key=settings.OPENROUTER_API_KEY,
            anthropic_key=settings.ANTHROPIC_API_KEY,
            ollama_model=settings.LLM_MODEL,
        ),
        chunker=HybridChunker(),
        loaders=LoaderFactory(),
    )
