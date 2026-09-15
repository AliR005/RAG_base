"""RetrieveUseCase: embed -> гибридный поиск -> реранкинг.

Конвейер: эмбеддинг запроса -> Qdrant prefetch top-30 (dense+sparse,
RRF внутри стора) -> кросс-энкодер -> top-k в контекст LLM.
"""

from __future__ import annotations

from app.adapters.reranker.bge_reranker import BgeReranker
from app.ports.embedding_provider import EmbeddingProvider
from app.ports.vector_store import ScoredChunk, VectorStoreRepository

CANDIDATE_LIMIT = 30


class RetrieveUseCase:
    def __init__(
        self,
        vectors: VectorStoreRepository,
        embeddings: EmbeddingProvider,
        reranker: BgeReranker | None = None,
    ):
        self.vectors = vectors
        self.embeddings = embeddings
        self.reranker = reranker

    async def execute(
        self,
        query: str,
        user_id: str,
        top_k: int = 5,
        candidate_limit: int = CANDIDATE_LIMIT,
    ) -> list[ScoredChunk]:
        query_embedding = await self.embeddings.embed_query(query)
        candidates = await self.vectors.search(
            query, query_embedding, user_id, top_k=candidate_limit
        )
        if not self.reranker or not candidates:
            return candidates[:top_k]
        reranked = await self.reranker.rerank(
            query, [c.chunk for c in candidates], top_k=top_k
        )
        return [
            ScoredChunk(chunk=chunk, score=score) for chunk, score in reranked
        ]
