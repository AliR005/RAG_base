"""ChatUseCase: retrieve -> промпт -> стрим ответа + citations."""

from __future__ import annotations

from collections.abc import AsyncIterator
from pathlib import Path

import yaml
from app.application.retrieve import RetrieveUseCase
from app.core.config import BASE_DIR
from app.domain.chat import ChatMessage, Citation
from app.ports.llm_provider import LLMProvider
from app.services.history import format_history

TEMPLATE_PATH = BASE_DIR / "template.yaml"


def load_prompt_template(path: Path = TEMPLATE_PATH) -> str:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)["prompt"]


def build_prompt(
    template: str,
    query: str,
    context_chunks: list[str],
    history: list[ChatMessage],
) -> str:
    return template.format(
        chat_history=format_history(history) if history else "",
        question=query,
        context="\n\n[DOC]\n\n".join(context_chunks),
    )


class ChatUseCase:
    """Стриминг ответа поверх retrieval. История сохраняется слоем API."""

    def __init__(
        self,
        retrieve: RetrieveUseCase,
        llm: LLMProvider,
        template: str | None = None,
    ):
        self.retrieve = retrieve
        self.llm = llm
        self._template = template

    def _template_or_load(self) -> str:
        if self._template is None:
            self._template = load_prompt_template()
        return self._template

    async def answer(
        self,
        query: str,
        history: list[ChatMessage],
        user_id: str,
        model: str,
        top_k: int = 5,
    ) -> tuple[str, list[Citation]]:
        """Нестриминговый ответ: полный текст + источники."""
        full, citations = "", []
        async for event in self.stream(query, history, user_id, model, top_k):
            if event["type"] == "token":
                full += event["token"]
            elif event["type"] == "done":
                citations = event["sources"]
        return full, citations

    async def stream(
        self,
        query: str,
        history: list[ChatMessage],
        user_id: str,
        model: str,
        top_k: int = 5,
    ) -> AsyncIterator[dict]:
        """События: {"type": "token", "token": ...} ... {"type": "done",
        "sources": [Citation, ...]}."""
        scored = await self.retrieve.execute(query, user_id, top_k=top_k)
        citations = [
            Citation(
                chunk_id=s.chunk.id,
                document_id=s.chunk.document_id,
                title=s.chunk.title,
                url=s.chunk.url,
                snippet=s.chunk.content[:300],
            )
            for s in scored
        ]
        prompt = build_prompt(
            self._template_or_load(),
            query,
            [s.chunk.content for s in scored],
            history,
        )
        prompt_msg = ChatMessage(
            id="prompt", chat_id="", role="user", content=prompt
        )
        async for token in self.llm.generate(
            [*history, prompt_msg], model=model, stream=True
        ):
            yield {"type": "token", "token": token}
        yield {"type": "done", "sources": citations}
