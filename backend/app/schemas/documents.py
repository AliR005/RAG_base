"""Схемы документов."""

from datetime import datetime

from pydantic import BaseModel


class DocumentCreate(BaseModel):
    url: str


class DocumentOut(BaseModel):
    id: str
    source_type: str
    origin: str
    title: str | None = None
    status: str
    error: str | None = None
    created_at: datetime
