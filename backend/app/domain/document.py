"""Доменные сущности ingestion: документы и чанки. Чистый Python."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class SourceType(str, Enum):
    FILE = "file"
    URL = "url"
    YOUTUBE = "youtube"


class DocumentStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    DONE = "done"
    ERROR = "error"


@dataclass
class Document:
    """Трекинг ingestion в Postgres. Сами чанки живут в Qdrant."""

    id: str
    user_id: str
    source_type: SourceType
    origin: str  # путь к файлу, URL статьи или URL видео
    status: DocumentStatus = DocumentStatus.PENDING
    title: str | None = None
    content_hash: str | None = None
    error: str | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Chunk:
    """Фрагмент документа с метаданными для payload Qdrant."""

    id: str
    document_id: str
    content: str
    ordinal: int = 0
    title: str | None = None
    section: str | None = None
    url: str | None = None
    metadata: dict = field(default_factory=dict)
