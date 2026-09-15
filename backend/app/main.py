import asyncio
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.container import AppContainer, build_container
from app.core.dependencies import (
    get_chat_repository,
    get_document_repository,
    get_llm_factory,
    get_qdrant_store,
    get_retrieve_usecase,
    get_user_repository,
)
from app.core.logging import configure_logging, get_logger
from app.core.middleware import RequestIdMiddleware
from app.core.rate_limit import limiter
from app.routers.auth import router as auth_router
from app.routers.chats import router as chats_router
from app.routers.documents import router as documents_router
from app.routers.models import router as models_router
from app.routers.stream import router as stream_router
from fastapi import FastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

configure_logging()
log = get_logger("app")


def _run_migrations() -> None:
    from alembic import command
    from alembic.config import Config

    cfg = Config("alembic.ini")
    cfg.set_main_option("script_location", "alembic")
    command.upgrade(cfg, "head")


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await asyncio.to_thread(_run_migrations)
        container: AppContainer | None = build_container(settings)
        app.state.container = container
        app.dependency_overrides[get_user_repository] = lambda: container.users
        app.dependency_overrides[get_chat_repository] = lambda: container.chats
        app.dependency_overrides[get_document_repository] = (
            lambda: container.documents
        )
        app.dependency_overrides[get_qdrant_store] = lambda: container.vectors
        app.dependency_overrides[get_llm_factory] = (
            lambda: container.llm_factory
        )
        app.dependency_overrides[get_retrieve_usecase] = (
            lambda: container.retrieve()
        )
        print("Postgres wired: repositories use Postgres")
    except Exception as e:
        app.state.container = None
        log.warning("postgres_unavailable", error=str(e))
    yield


app = FastAPI(
    title="ДагГАУ Чат-бот",
    description="RAG-система для абитуриентов и студентов",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(stream_router)
app.include_router(auth_router)
app.include_router(chats_router)
app.include_router(models_router)
app.include_router(documents_router)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(RequestIdMiddleware)


@app.get("/health")
async def health():
    return {"status": "ok"}
