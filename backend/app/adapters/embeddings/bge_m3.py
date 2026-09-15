"""BgeM3EmbeddingProvider: dense-эмбеддинги BAAI/bge-m3.

Модель тяжёлая — загрузка ленивая, в отдельном потоке.
Sparse-компонента (BM25) считается в Qdrant-адаптере через fastembed.
"""

from __future__ import annotations

import asyncio

BGE_M3_DIM = 1024


class BgeM3EmbeddingProvider:
    """Адаптер EmbeddingProvider на sentence-transformers."""

    def __init__(self, model_id: str = "BAAI/bge-m3"):
        self.model_id = model_id
        self._model = None

    @property
    def dense_dim(self) -> int:
        return BGE_M3_DIM

    def _load(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self.model_id)
        return self._model

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        model = await asyncio.to_thread(self._load)
        vectors = await asyncio.to_thread(model.encode, texts)
        return [v.tolist() for v in vectors]

    async def embed_query(self, query: str) -> list[float]:
        vectors = await self.embed_texts([query])
        return vectors[0]
