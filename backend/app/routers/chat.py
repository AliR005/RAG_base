from app.core.dependencies import get_llm, get_vector_store
from app.db.vector_store import VectorStore
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.llm import LLMAssistant
from app.services.rag import get_rag_answer
from fastapi import APIRouter, Depends

router = APIRouter()


@router.post("/query/", response_model=ChatResponse)
async def query(
    request: ChatRequest,
    db: VectorStore = Depends(get_vector_store),
    llm: LLMAssistant = Depends(get_llm),
) -> ChatResponse:
    answer = await get_rag_answer(request.query, request.history, db, llm)
    return ChatResponse(answer=answer)
