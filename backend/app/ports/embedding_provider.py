"""Порт провайдера эмбеддингов: текст -> векторы."""

from __future__ import annotations

from typing import Protocol


class EmbeddingProvider(Protocol):
    @property
    def dense_dim(self) -> int:
        """Размерность dense-вектора."""
        ...

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Эмбеддинги чанков для записи."""
        ...

    async def embed_query(self, query: str) -> list[float]:
        """Эмбеддинг поискового запроса."""
        ...
