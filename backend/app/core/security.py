"""Безопасность: bcrypt-пароли и JWT access-токены."""

from __future__ import annotations

from datetime import datetime, timedelta

import bcrypt
import jwt

ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode(
        "utf-8"
    )


def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        return False


def create_access_token(
    user_id: str, secret: str, expires_minutes: int = 60
) -> str:
    now = datetime.utcnow()
    payload = {
        "sub": user_id,
        "iat": now,
        "exp": now + timedelta(minutes=expires_minutes),
    }
    return jwt.encode(payload, secret, algorithm=ALGORITHM)


def decode_access_token(token: str, secret: str) -> str:
    """Вернуть user_id (sub). Бросает jwt.PyJWTError при проблеме."""
    payload = jwt.decode(token, secret, algorithms=[ALGORITHM])
    return str(payload["sub"])
