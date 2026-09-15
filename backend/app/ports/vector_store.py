"""Порт векторного хранилища: запись/поиск/удаление чанков."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from app.domain.document import Chunk


@dataclass
class ScoredChunk:
    chunk: Chunk
    score: float


class VectorStoreRepository(Protocol):
    async def add(
        self, chunks: list[Chunk], embeddings: list[list[float]]
    ) -> None:
        """Записать чанки с dense-эмбеддингами (sparse — внутри)."""
        ...

    async def search(
        self,
        query: str,
        query_embedding: list[float],
        user_id: str,
        top_k: int = 5,
    ) -> list[ScoredChunk]:
        """Гибридный поиск с фильтрацией по пользователю."""
        ...

    async def delete_by_document(self, document_id: str) -> None:
        """Удалить все чанки документа."""
        ...
