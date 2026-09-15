"""Unit: security (bcrypt/JWT) и SSE-парсинг OpenRouter."""

import jwt
import pytest
from app.adapters.llm.openrouter_provider import parse_sse_line
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)

SECRET = "test-secret-key-long-enough-for-hs256-ok"


def test_password_roundtrip():
    hashed = hash_password("secret123")
    assert hashed != "secret123"
    assert verify_password("secret123", hashed)
    assert not verify_password("wrong", hashed)


def test_token_roundtrip():
    token = create_access_token("uid1", SECRET, 60)
    assert decode_access_token(token, SECRET) == "uid1"


def test_token_wrong_secret_raises():
    token = create_access_token("uid1", SECRET, 60)
    with pytest.raises(jwt.PyJWTError):
        decode_access_token(token, "other-secret")


def test_parse_sse_token_line():
    line = 'data: {"choices": [{"delta": {"content": "привет"}}]}'
    assert parse_sse_line(line) == ["привет"]


@pytest.mark.parametrize(
    "line",
    ["data: [DONE]", ": ping", "", "event: message", "data: {broken"],
)
def test_parse_sse_ignores_non_token_lines(line):
    assert parse_sse_line(line) == []
