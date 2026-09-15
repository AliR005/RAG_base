"""DoclingLoader: файлы и веб-страницы -> markdown.

Покрывает pdf/docx/pptx/xlsx/html/md/изображения (OCR) локально
и произвольные URL (статья/страница/PDF по ссылке) — Docling
принимает URL напрямую. Тяжёлые импорты ленивые, чтобы модуль
импортировался без установленного docling.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

from app.domain.document import SourceType
from app.ports.document_loader import LoadedDocument

SUPPORTED_SUFFIXES = frozenset(
    {
        ".pdf",
        ".docx",
        ".pptx",
        ".xlsx",
        ".html",
        ".htm",
        ".md",
        ".markdown",
        ".png",
        ".jpg",
        ".jpeg",
        ".tiff",
        ".bmp",
    }
)


def _is_url(origin: str) -> bool:
    return origin.startswith(("http://", "https://"))


class DoclingLoader:
    """Адаптер DocumentLoader на Docling DocumentConverter."""

    source_type = SourceType.FILE

    def __init__(self, artifacts_path: str | None = None):
        self.artifacts_path = artifacts_path

    async def load(self, origin: str) -> LoadedDocument:
        if not _is_url(origin):
            suffix = Path(origin).suffix.lower()
            if suffix not in SUPPORTED_SUFFIXES:
                raise ValueError(
                    f"Unsupported file type: {suffix!r}. "
                    f"Supported: {sorted(SUPPORTED_SUFFIXES)}"
                )
        return await asyncio.to_thread(self._convert, origin)

    def _convert(self, origin: str) -> LoadedDocument:
        from docling.document_converter import DocumentConverter

        converter = DocumentConverter()
        result = converter.convert(origin)
        doc = result.document
        markdown = doc.export_to_markdown()
        title = doc.name or None
        return LoadedDocument(
            markdown=markdown,
            title=title,
            source_type=SourceType.URL if _is_url(origin) else SourceType.FILE,
            metadata={"origin": origin},
        )
