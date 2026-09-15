"""AnthropicProvider: нативный SDK."""

from __future__ import annotations

from collections.abc import AsyncIterator, Sequence

from app.domain.chat import ChatMessage


class AnthropicProvider:
    name = "anthropic"

    def __init__(self, api_key: str = ""):
        self.api_key = api_key

    async def generate(
        self,
        messages: Sequence[ChatMessage],
        model: str,
        stream: bool = True,
    ) -> AsyncIterator[str]:
        from anthropic import AsyncAnthropic

        client = AsyncAnthropic(api_key=self.api_key or None)
        payload = [{"role": m.role, "content": m.content} for m in messages]
        if not stream:
            response = await client.messages.create(
                model=model, max_tokens=4096, messages=payload
            )
            yield "".join(
                b.text
                for b in response.content
                if getattr(b, "type", "") == "text"
            )
            return
        async with client.messages.stream(
            model=model, max_tokens=4096, messages=payload
        ) as s:
            async for text in s.text_stream:
                yield text
