"""SSE-стриминг ответа: POST /query/stream.

События: `data: {"token": "..."}` ... `data: {"done": true, ...}`.
user_id пока передаётся в теле (изоляция выборки); с пункта 11/13
identity берётся из JWT.
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator

from app.adapters.llm.factory import LLMProviderFactory
from app.application.chat import ChatUseCase
from app.application.retrieve import RetrieveUseCase
from app.core.dependencies import (
    get_llm_factory,
    get_retrieve_usecase,
)
from app.domain.chat import ChatMessage
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

router = APIRouter()


class StreamMessage(BaseModel):
    role: str
    content: str


class StreamRequest(BaseModel):
    query: str
    history: list[StreamMessage] = []
    model_id: str = "local"
    user_id: str
    top_k: int = 5


async def _history(req: StreamRequest) -> list[ChatMessage]:
    return [
        ChatMessage(id=f"h{i}", chat_id="", role=m.role, content=m.content)
        for i, m in enumerate(req.history)
    ]


def _data(payload: dict) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


@router.post("/query/stream")
async def query_stream(
    req: StreamRequest,
    retrieve: RetrieveUseCase = Depends(get_retrieve_usecase),
    factory: LLMProviderFactory = Depends(get_llm_factory),
) -> StreamingResponse:
    provider, info = factory.resolve(req.model_id)
    usecase = ChatUseCase(retrieve=retrieve, llm=provider)

    async def gen() -> AsyncIterator[str]:
        history = await _history(req)
        async for event in usecase.stream(
            req.query,
            history,
            req.user_id,
            info.model,
            top_k=req.top_k,
        ):
            if event["type"] == "token":
                yield _data({"token": event["token"]})
            else:
                yield _data(
                    {
                        "done": True,
                        "sources": [
                            {
                                "chunk_id": c.chunk_id,
                                "document_id": c.document_id,
                                "title": c.title,
                                "url": c.url,
                                "snippet": c.snippet,
                            }
                            for c in event["sources"]
                        ],
                    }
                )

    return StreamingResponse(gen(), media_type="text/event-stream")
