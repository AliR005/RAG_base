"""Доменные сущности чата. Чистый Python."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Chat:
    id: str
    user_id: str
    title: str = "Новый чат"
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Citation:
    """Источник ответа: чанк/документ, из которого взят контекст."""

    chunk_id: str
    document_id: str
    title: str | None = None
    url: str | None = None
    snippet: str | None = None


@dataclass
class ChatMessage:
    id: str
    chat_id: str
    role: str  # "user" | "assistant"
    content: str
    model_used: str | None = None
    sources: list[Citation] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
