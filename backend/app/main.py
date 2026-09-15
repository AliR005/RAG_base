from contextlib import asynccontextmanager

from app.core.dependencies import get_llm, get_vector_store
from app.routers.auth import router as auth_router
from app.routers.chat import router as chat_router
from app.routers.stream import router as stream_router
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
app.include_router(stream_router)
app.include_router(auth_router)


@app.get("/health")
async def health():
    return {"status": "ok"}
