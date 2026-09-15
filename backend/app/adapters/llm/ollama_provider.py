"""OllamaProvider: локальный/офлайн адаптер (текущая интеграция)."""

from __future__ import annotations

from collections.abc import AsyncIterator, Sequence

from app.domain.chat import ChatMessage

OLLAMA_OPTIONS = {
    "temperature": 0.2,
    "num_ctx": 4096,
    "top_k": 40,
    "top_p": 0.9,
}


class OllamaProvider:
    name = "ollama"

    def __init__(self, default_model: str = ""):
        self.default_model = default_model

    async def generate(
        self,
        messages: Sequence[ChatMessage],
        model: str,
        stream: bool = True,
    ) -> AsyncIterator[str]:
        import ollama

        payload = [{"role": m.role, "content": m.content} for m in messages]
        chosen = model or self.default_model
        if not stream:
            response = ollama.chat(
                model=chosen, messages=payload, options=OLLAMA_OPTIONS
            )
            yield response["message"]["content"]
            return
        chunks = ollama.chat(
            model=chosen,
            messages=payload,
            options=OLLAMA_OPTIONS,
            stream=True,
        )
        for part in chunks:
            text = part["message"]["content"]
            if text:
                yield text
