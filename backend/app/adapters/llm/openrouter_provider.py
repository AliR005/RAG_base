"""OpenRouterProvider: один ключ -> десятки моделей.

OpenAI-совместимый /chat/completions, модель выбирается строкой
model-id из реестра. Стриминг — нативный SSE через httpx.
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator, Sequence

import httpx
from app.domain.chat import ChatMessage

BASE_URL = "https://openrouter.ai/api/v1"


class OpenRouterProvider:
    name = "openrouter"

    def __init__(
        self,
        api_key: str = "",
        base_url: str = BASE_URL,
        timeout: float = 120.0,
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    async def generate(
        self,
        messages: Sequence[ChatMessage],
        model: str,
        stream: bool = True,
    ) -> AsyncIterator[str]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model,
            "messages": [
                {"role": m.role, "content": m.content} for m in messages
            ],
            "stream": stream,
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            if not stream:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
                yield data["choices"][0]["message"]["content"]
                return
            async with client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    for token in parse_sse_line(line):
                        yield token


def parse_sse_line(line: str) -> list[str]:
    """Чистая функция: одна SSE-строка -> список токенов."""
    line = line.strip()
    if not line.startswith("data:"):
        return []
    data = line[5:].strip()
    if data == "[DONE]":
        return []
    try:
        event = json.loads(data)
    except json.JSONDecodeError:
        return []
    tokens = []
    for choice in event.get("choices", []):
        text = (choice.get("delta") or {}).get("content")
        if text:
            tokens.append(text)
    return tokens
