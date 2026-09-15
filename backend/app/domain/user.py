"""Доменная сущность пользователя. Чистый Python."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class User:
    id: str
    email: str
    hashed_password: str
    created_at: datetime = field(default_factory=datetime.utcnow)
