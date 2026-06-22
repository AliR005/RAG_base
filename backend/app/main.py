from contextlib import asynccontextmanager

from app.core.dependencies import get_llm, get_vector_store
from app.routers.chat import router as chat_router
from fastapi import FastAPI


@asynccontextmanager
async def lifespan(app: FastAPI):
    get_vector_store()
    get_llm()
    yield


app = FastAPI(
    title="ДагГАУ Чат-бот",
    description="RAG-система для абитуриентов и студентов",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(chat_router)


@app.get("/health")
async def health():
    return {"status": "ok"}
