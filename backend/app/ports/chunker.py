"""Порт чанкера: markdown -> список чанков."""

from __future__ import annotations

from typing import Protocol

from app.domain.document import Chunk


class Chunker(Protocol):
    async def chunk(
        self,
        markdown: str,
        document_id: str,
        title: str | None = None,
        url: str | None = None,
    ) -> list[Chunk]:
        """Разбить markdown на чанки с метаданными документа."""
        ...
