"""Чаты: CRUD, история, отправка сообщения (SSE + персистентность).

Отправка: user-сообщение сохраняется сразу, ответ стримятся токенами,
по завершении assistant-сообщение сохраняется с model_used и sources.
"""

from __future__ import annotations

import json
import uuid
from collections.abc import AsyncIterator

from app.application.chat import ChatUseCase
from app.core.dependencies import (
    get_chat_repository,
    get_llm_factory,
    get_retrieve_usecase,
)
from app.domain.chat import ChatMessage, Citation
from app.domain.user import User
from app.ports.repositories import ChatRepository
from app.routers.auth import get_current_user
from app.schemas.chats import (
    ChatCreate,
    ChatOut,
    ChatRename,
    CitationOut,
    MessageOut,
    SendMessageRequest,
)
from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/chats", tags=["chats"])


def _chat_out(chat) -> ChatOut:
    return ChatOut(
        id=chat.id,
        title=chat.title,
        created_at=chat.created_at,
        updated_at=chat.updated_at,
    )


def _message_out(msg: ChatMessage) -> MessageOut:
    return MessageOut(
        id=msg.id,
        role=msg.role,
        content=msg.content,
        model_used=msg.model_used,
        sources=[
            CitationOut(
                chunk_id=c.chunk_id,
                document_id=c.document_id,
                title=c.title,
                url=c.url,
                snippet=c.snippet,
            )
            for c in msg.sources
        ],
        created_at=msg.created_at,
    )


@router.post("", response_model=ChatOut, status_code=201)
async def create_chat(
    body: ChatCreate,
    user: User = Depends(get_current_user),
    chats: ChatRepository = Depends(get_chat_repository),
) -> ChatOut:
    return _chat_out(await chats.create_chat(user.id, body.title))


@router.get("", response_model=list[ChatOut])
async def list_chats(
    user: User = Depends(get_current_user),
    chats: ChatRepository = Depends(get_chat_repository),
) -> list[ChatOut]:
    return [_chat_out(c) for c in await chats.list_chats(user.id)]


@router.patch("/{chat_id}", response_model=ChatOut)
async def rename_chat(
    chat_id: str,
    body: ChatRename,
    user: User = Depends(get_current_user),
    chats: ChatRepository = Depends(get_chat_repository),
) -> ChatOut:
    chat = await chats.rename_chat(chat_id, user.id, body.title)
    if chat is None:
        raise HTTPException(status_code=404, detail="Chat not found")
    return _chat_out(chat)


@router.delete("/{chat_id}", status_code=204)
async def delete_chat(
    chat_id: str,
    user: User = Depends(get_current_user),
    chats: ChatRepository = Depends(get_chat_repository),
) -> Response:
    if not await chats.delete_chat(chat_id, user.id):
        raise HTTPException(status_code=404, detail="Chat not found")
    return Response(status_code=204)


@router.get("/{chat_id}/messages", response_model=list[MessageOut])
async def list_messages(
    chat_id: str,
    user: User = Depends(get_current_user),
    chats: ChatRepository = Depends(get_chat_repository),
) -> list[MessageOut]:
    if await chats.get_chat(chat_id, user.id) is None:
        raise HTTPException(status_code=404, detail="Chat not found")
    return [
        _message_out(m) for m in await chats.list_messages(chat_id, user.id)
    ]


@router.post("/{chat_id}/messages")
async def send_message(
    chat_id: str,
    body: SendMessageRequest,
    user: User = Depends(get_current_user),
    chats: ChatRepository = Depends(get_chat_repository),
    retrieve=Depends(get_retrieve_usecase),
    llm_factory=Depends(get_llm_factory),
) -> StreamingResponse:
    if await chats.get_chat(chat_id, user.id) is None:
        raise HTTPException(status_code=404, detail="Chat not found")
    provider, info = llm_factory.resolve(body.model_id)
    usecase = ChatUseCase(retrieve=retrieve, llm=provider)

    async def gen() -> AsyncIterator[str]:
        await chats.add_message(
            ChatMessage(
                id=uuid.uuid4().hex,
                chat_id=chat_id,
                role="user",
                content=body.query,
            )
        )
        history = await chats.list_messages(chat_id, user.id)
        full, citations = "", []
        async for event in usecase.stream(
            body.query,
            history,
            user.id,
            info.model,
            top_k=body.top_k,
        ):
            if event["type"] == "token":
                full += event["token"]
                yield _data({"token": event["token"]})
            else:
                citations = event["sources"]
        await chats.add_message(
            ChatMessage(
                id=uuid.uuid4().hex,
                chat_id=chat_id,
                role="assistant",
                content=full,
                model_used=body.model_id,
                sources=citations,
            )
        )
        yield _data(
            {
                "done": True,
                "sources": [_citation_dict(c) for c in citations],
            }
        )

    return StreamingResponse(gen(), media_type="text/event-stream")


def _data(payload: dict) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


def _citation_dict(c: Citation) -> dict:
    return {
        "chunk_id": c.chunk_id,
        "document_id": c.document_id,
        "title": c.title,
        "url": c.url,
        "snippet": c.snippet,
    }
