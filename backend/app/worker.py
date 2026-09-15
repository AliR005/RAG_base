"""arq-воркер ingestion: асинхронная обработка документов.

Запуск: `arq app.worker.WorkerSettings` (нужен запущенный Redis
из docker-compose). Конкретные зависимости (use-case с реальными
адаптерами) подкладываются в ctx через startup при сборке
контейнера зависимостей — до тех пор job падает с понятной ошибкой.
"""

from __future__ import annotations

import os
from collections.abc import Callable

from app.application.ingest import IngestDocumentUseCase
from arq.connections import RedisSettings

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")


async def startup(ctx: dict) -> None:
    """Собрать реальный use-case из container. Тяжёлое: модели грузятся
    лениво при первом вызове, но Postgres/Qdrant должны быть доступны."""
    from app.core.config import settings
    from app.core.container import build_container

    container = build_container(settings)
    ctx["usecase_factory"] = container.ingest


async def ingest_document(ctx: dict, document_id: str, user_id: str) -> None:
    factory: Callable[[], IngestDocumentUseCase] | None = ctx.get(
        "usecase_factory"
    )
    if factory is None:
        raise RuntimeError(
            "Worker is not wired: set ctx['usecase_factory'] in "
            "startup to a callable returning IngestDocumentUseCase"
        )
    await factory().execute(document_id, user_id)


async def enqueue_ingest(
    redis_url: str, document_id: str, user_id: str
) -> str:
    """Поставить документ в очередь. Возвращает id job'а."""
    from arq import create_pool
    from arq.connections import RedisSettings

    pool = await create_pool(RedisSettings.from_dsn(redis_url))
    try:
        job = await pool.enqueue_job("ingest_document", document_id, user_id)
        return job.job_id
    finally:
        await pool.close()


class WorkerSettings:
    functions = [ingest_document]
    on_startup = startup
    # NB: arq читает это поле как готовый RedisSettings (create_pool
    # обращается к .host/.port). Вариант "@staticmethod def
    # redis_settings()" arq не вызывает — падает AttributeError:
    # 'staticmethod' object has no attribute 'host'.
    redis_settings = RedisSettings.from_dsn(os.getenv("REDIS_URL", REDIS_URL))
