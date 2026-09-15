"""Схемы CRUD чатов."""

from datetime import datetime

from pydantic import BaseModel


class ChatCreate(BaseModel):
    title: str = "Новый чат"


class ChatRename(BaseModel):
    title: str


class CitationOut(BaseModel):
    chunk_id: str
    document_id: str
    title: str | None = None
    url: str | None = None
    snippet: str | None = None


class MessageOut(BaseModel):
    id: str
    role: str
    content: str
    model_used: str | None = None
    sources: list[CitationOut] = []
    created_at: datetime


class ChatOut(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime


class SendMessageRequest(BaseModel):
    query: str
    model_id: str = "local"
    top_k: int = 5
