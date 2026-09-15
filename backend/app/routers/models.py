"""Реестр моделей для выпадающего списка в UI: GET /models."""

from app.adapters.llm.factory import load_registry
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["models"])


class ModelOut(BaseModel):
    id: str
    name: str
    provider: str
    context_window: int


@router.get("/models", response_model=list[ModelOut])
async def list_models() -> list[ModelOut]:
    return [
        ModelOut(
            id=m.id,
            name=m.name,
            provider=m.provider,
            context_window=m.context_window,
        )
        for m in load_registry()
    ]
