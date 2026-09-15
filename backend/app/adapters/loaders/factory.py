"""LoaderFactory: выбор загрузчика по типу источника (Strategy)."""

from __future__ import annotations

from app.adapters.loaders.docling_loader import DoclingLoader
from app.adapters.loaders.youtube_loader import (
    YouTubeLoader,
    is_youtube_url,
)
from app.domain.document import SourceType
from app.ports.document_loader import DocumentLoader


def detect_source_type(origin: str) -> SourceType:
    """Чистая функция роутинга — покрыта unit-тестами."""
    if is_youtube_url(origin):
        return SourceType.YOUTUBE
    if origin.startswith(("http://", "https://")):
        return SourceType.URL
    return SourceType.FILE


class LoaderFactory:
    """Factory: источник -> готовый DocumentLoader."""

    def __init__(
        self,
        docling_loader: DocumentLoader | None = None,
        youtube_loader: DocumentLoader | None = None,
    ):
        self._docling = docling_loader or DoclingLoader()
        self._youtube = youtube_loader or YouTubeLoader()

    def get(self, origin: str) -> DocumentLoader:
        source = detect_source_type(origin)
        if source == SourceType.YOUTUBE:
            return self._youtube
        return self._docling
