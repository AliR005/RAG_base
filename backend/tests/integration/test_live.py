"""Live-интеграция с реальными Postgres/Qdrant.

Запуск: RAG_LIVE=1 pytest backend/tests/integration/test_live.py
Требует поднятый `docker compose up` (postgres, qdrant).
"""

import os
import random

import pytest

pytestmark = pytest.mark.skipif(
    os.getenv("RAG_LIVE") != "1",
    reason="Требует живые сервисы: RAG_LIVE=1",
)


def test_postgres_repositories_live():
    from app.adapters.db.postgres import (
        PostgresChatRepository,
        PostgresDocumentRepository,
        PostgresUserRepository,
        make_session_factory,
    )
    from app.core.security import hash_password
    from app.domain.chat import ChatMessage, Citation
    from app.domain.document import Document, DocumentStatus, SourceType
    from sqlalchemy import text
    from tests.conftest import run

    async def scenario():
        sessions = make_session_factory(
            "postgresql+asyncpg://rag:rag@localhost:5432/rag"
        )
        users = PostgresUserRepository(sessions)
        chats = PostgresChatRepository(sessions)
        docs = PostgresDocumentRepository(sessions)
        email = "live@x.ru"
        async with sessions() as s:
            await s.execute(
                text("DELETE FROM users WHERE email=:e"), {"e": email}
            )
            await s.commit()
        user = await users.create(email, hash_password("pw"))
        chat = await chats.create_chat(user.id, "live")
        await chats.add_message(
            ChatMessage(id="", chat_id=chat.id, role="user", content="hi")
        )
        await chats.add_message(
            ChatMessage(
                id="",
                chat_id=chat.id,
                role="assistant",
                content="hello",
                model_used="local",
                sources=[Citation(chunk_id="d_0", document_id="d")],
            )
        )
        messages = await chats.list_messages(chat.id, user.id)
        assert len(messages) == 2
        assert messages[1].sources[0].chunk_id == "d_0"
        doc = await docs.create(
            Document(
                id="",
                user_id=user.id,
                source_type=SourceType.FILE,
                origin="/tmp/x.md",
            )
        )
        await docs.set_status(doc.id, DocumentStatus.DONE)
        assert (await docs.get(doc.id, user.id)).status == DocumentStatus.DONE
        await docs.delete(doc.id, user.id)
        await chats.delete_chat(chat.id, user.id)
        async with sessions() as s:
            await s.execute(
                text("DELETE FROM users WHERE email=:e"), {"e": email}
            )
            await s.commit()

    run(scenario())


def test_qdrant_live():
    import types

    import numpy as np
    from app.adapters.vector_store.qdrant_store import QdrantVectorStore
    from app.domain.document import Chunk
    from qdrant_client import QdrantClient
    from tests.conftest import run

    class Sparse:
        def __init__(self):
            self.indices = np.array([1])
            self.values = np.array([0.5])

    async def scenario():
        store = QdrantVectorStore(collection="test_live_pytest")
        store._sparse_model = types.SimpleNamespace(
            embed=lambda texts: [Sparse() for _ in texts]
        )
        await store.ensure_collection()
        chunks = [
            Chunk(id="live_0", document_id="live", content="агрономия и почвы")
        ]
        vec = [[random.random() for _ in range(1024)]]
        await store.add(chunks, vec, user_id="live-user")
        res = await store.search("почвы", vec[0], "live-user", top_k=1)
        assert len(res) == 1
        assert res[0].chunk.content == "агрономия и почвы"
        assert await store.search("почвы", vec[0], "чужой") == []
        await store.delete_by_document("live")
        assert await store.search("почвы", vec[0], "live-user") == []
        QdrantClient(url="http://localhost:6333").delete_collection(
            "test_live_pytest"
        )

    run(scenario())
