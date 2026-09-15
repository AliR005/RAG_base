"""Порт загрузчика документов: источник -> markdown + метаданные."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from app.domain.document import SourceType


@dataclass
class LoadedDocument:
    """Нормализованный результат загрузчика."""

    markdown: str
    title: str | None = None
    source_type: SourceType = SourceType.FILE
    metadata: dict = field(default_factory=dict)


class DocumentLoader(Protocol):
    """Strategy: один адаптер на тип источника."""

    source_type: SourceType

    async def load(self, origin: str) -> LoadedDocument:
        """Загрузить источник (путь/URL) и вернуть markdown."""
        ...
