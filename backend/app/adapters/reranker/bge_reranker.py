"""BgeReranker: кросс-энкодер bge-reranker-v2-m3 поверх кандидатов."""

from __future__ import annotations

import asyncio

from app.domain.document import Chunk


def order_by_score(
    chunks: list[Chunk], scores: list[float], top_k: int
) -> list[tuple[Chunk, float]]:
    """Чистая функция: сортировка по скору и срез top-k."""
    ranked = sorted(
        zip(chunks, scores), key=lambda pair: pair[1], reverse=True
    )
    return ranked[:top_k]


class BgeReranker:
    """Реранкинг top-N кандидатов гибридного поиска."""

    def __init__(self, model_id: str = "BAAI/bge-reranker-v2-m3"):
        self.model_id = model_id
        self._model = None

    def _load(self):
        if self._model is None:
            from sentence_transformers import CrossEncoder

            self._model = CrossEncoder(self.model_id)
        return self._model

    async def rerank(
        self, query: str, chunks: list[Chunk], top_k: int = 5
    ) -> list[tuple[Chunk, float]]:
        if not chunks:
            return []
        pairs = [(query, c.content) for c in chunks]
        model = await asyncio.to_thread(self._load)
        scores = await asyncio.to_thread(model.predict, pairs)
        return order_by_score(chunks, list(scores), top_k)
