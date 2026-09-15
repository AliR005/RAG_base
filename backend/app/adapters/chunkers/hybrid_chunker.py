"""HybridChunker: token-aware чанкинг через Docling.

Учитывает токенизатор эмбеддинг-модели, сохраняет структуру
(заголовки -> title/section, таблицы остаются в markdown чанка).
Замена старому сплиту по маркеру `##`.
"""

from __future__ import annotations

import asyncio
import uuid
from io import BytesIO

from app.domain.document import Chunk


def dl_chunk_to_chunk(
    dl_chunk, document_id: str, ordinal: int, url: str | None = None
) -> Chunk:
    """Чистая функция: Docling-чанк -> доменный Chunk.

    Отделена для тестируемости без docling: достаточно duck-typing
    объектов с `.text` и `.meta.headings`.
    """
    text = dl_chunk.text.strip()
    headings = getattr(dl_chunk.meta, "headings", None) or []
    title = headings[0] if headings else None
    section = " / ".join(headings) if headings else None
    return Chunk(
        id=f"{document_id}_{ordinal}",
        document_id=document_id,
        content=text,
        ordinal=ordinal,
        title=title,
        section=section,
        url=url,
        metadata={"headings": list(headings)},
    )


class HybridChunker:
    """Адаптер Chunker на docling HybridChunker."""

    def __init__(
        self,
        tokenizer_model: str = "BAAI/bge-m3",
        max_tokens: int = 512,
    ):
        self.tokenizer_model = tokenizer_model
        self.max_tokens = max_tokens

    async def chunk(
        self,
        markdown: str,
        document_id: str,
        title: str | None = None,
        url: str | None = None,
    ) -> list[Chunk]:
        chunks = await asyncio.to_thread(
            self._split, markdown, document_id, url
        )
        if title:
            for ch in chunks:
                if ch.title is None:
                    ch.title = title
        return chunks

    def _make_chunker(self):
        from docling.chunking import HybridChunker as DoclingChunker
        from docling_core.transforms.chunker.tokenizer.hf import (
            HuggingFaceTokenizer,
        )
        from transformers import AutoTokenizer

        tokenizer = HuggingFaceTokenizer(
            tokenizer=AutoTokenizer.from_pretrained(self.tokenizer_model),
            max_tokens=self.max_tokens,
        )
        return DoclingChunker(tokenizer=tokenizer)

    def _split(
        self, markdown: str, document_id: str, url: str | None
    ) -> list[Chunk]:
        from docling.dataclasses import DocumentStream
        from docling.document_converter import DocumentConverter

        stream = DocumentStream(
            name="document.md",
            mime_type="text/markdown",
            stream=BytesIO(markdown.encode("utf-8")),
        )
        doc = DocumentConverter().convert(stream).document
        chunker = self._make_chunker()
        chunk_iter = chunker.chunk(dl_doc=doc)
        return [
            dl_chunk_to_chunk(c, document_id, i, url)
            for i, c in enumerate(chunk_iter)
            if c.text and c.text.strip()
        ]


def new_chunk_id() -> str:
    return uuid.uuid4().hex
