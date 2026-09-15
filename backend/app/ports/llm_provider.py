"""Порт LLM-провайдера: сообщения -> (стрим) текст."""

from __future__ import annotations

from collections.abc import AsyncIterator, Sequence
from typing import Protocol

from app.domain.chat import ChatMessage


class LLMProvider(Protocol):
    name: str

    async def generate(
        self,
        messages: Sequence[ChatMessage],
        model: str,
        stream: bool = True,
    ) -> AsyncIterator[str]:
        """Стрим токенов ответа; при stream=False — один чанк."""
        ...
        yield ""  # делает метод асинхронным генератором для typing
