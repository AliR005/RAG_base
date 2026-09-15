from __future__ import annotations

from typing import TYPE_CHECKING

from app.core.dependencies import get_llm, get_vector_store
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.rag import get_rag_answer
from fastapi import APIRouter, Depends

if TYPE_CHECKING:
    from app.db.vector_store import VectorStore
    from app.services.llm import LLMAssistant

router = APIRouter()


@router.post("/query/", response_model=ChatResponse)
async def query(
    request: ChatRequest,
    db: VectorStore = Depends(get_vector_store),
    llm: LLMAssistant = Depends(get_llm),
) -> ChatResponse:
    answer = await get_rag_answer(request.query, request.history, db, llm)
    return ChatResponse(answer=answer)
