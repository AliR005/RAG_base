"""Integration: API поверх in-memory репозиториев и фейков.

lifespan приложения отключён (без Postgres/моделей), зависимости
подменены синглтонами. Проверяются HTTP-контракты и изоляция
данных между пользователями.
"""

import json
from contextlib import asynccontextmanager

import pytest
from app.adapters.db.memory import (
    InMemoryChatRepository,
    InMemoryDocumentRepository,
    InMemoryUserRepository,
)
from app.adapters.llm.factory import LLMProviderFactory
from app.application.retrieve import RetrieveUseCase
from app.core.dependencies import (
    get_chat_repository,
    get_document_repository,
    get_llm_factory,
    get_qdrant_store,
    get_retrieve_usecase,
    get_user_repository,
)
from app.domain.document import Chunk
from app.main import app
from app.ports.vector_store import ScoredChunk
from fastapi.testclient import TestClient


class FakeEmb:
    async def embed_query(self, query):
        return [1.0]

    async def embed_texts(self, texts):
        return [[1.0] for _ in texts]


class FakeStore:
    def __init__(self):
        self.deleted = []

    async def add(self, chunks, embeddings, user_id=""):
        pass

    async def search(self, query, embedding, user_id, top_k=5):
        return [
            ScoredChunk(
                chunk=Chunk(
                    id="d_0",
                    document_id="doc1",
                    content="контекст",
                    title="Doc",
                ),
                score=0.9,
            )
        ]

    async def delete_by_document(self, document_id):
        self.deleted.append(document_id)


class FakeLLM:
    name = "fake"

    async def generate(self, messages, model, stream=True):
        yield "Ответ"


@asynccontextmanager
async def _noop_lifespan(application):
    yield


@pytest.fixture()
def client():
    app.router.lifespan_context = _noop_lifespan
    users = InMemoryUserRepository()
    chats = InMemoryChatRepository()
    docs = InMemoryDocumentRepository()
    vectors = FakeStore()
    app.dependency_overrides[get_user_repository] = lambda: users
    app.dependency_overrides[get_chat_repository] = lambda: chats
    app.dependency_overrides[get_document_repository] = lambda: docs
    app.dependency_overrides[get_qdrant_store] = lambda: vectors
    app.dependency_overrides[get_retrieve_usecase] = lambda: RetrieveUseCase(
        vectors, FakeEmb(), None
    )
    app.dependency_overrides[get_llm_factory] = lambda: LLMProviderFactory(
        providers={"ollama": FakeLLM()}
    )
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
    app.dependency_overrides.clear()


def _auth(client, email):
    client.post(
        "/auth/register",
        json={"email": email, "password": "pw123456"},
    )
    token = client.post(
        "/auth/login", json={"email": email, "password": "pw123456"}
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_register_login_me(client):
    email = "api1@x.ru"
    r = client.post(
        "/auth/register",
        json={"email": email, "password": "pw123456"},
    )
    assert r.status_code == 201
    assert (
        client.post(
            "/auth/register",
            json={"email": email, "password": "pw123456"},
        ).status_code
        == 409
    )
    token = client.post(
        "/auth/login", json={"email": email, "password": "pw123456"}
    ).json()["access_token"]
    r = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200 and r.json()["email"] == email
    assert client.get("/auth/me").status_code == 401


def test_chats_crud_and_isolation(client):
    alice, bob = _auth(client, "alice@x.ru"), _auth(client, "bob@x.ru")
    cid = client.post("/chats", json={"title": "A"}, headers=alice).json()[
        "id"
    ]
    assert len(client.get("/chats", headers=alice).json()) == 1
    assert client.get("/chats", headers=bob).json() == []
    # чужой чат невидим
    assert client.get(f"/chats/{cid}/messages", headers=bob).status_code == 404
    assert (
        client.patch(
            f"/chats/{cid}", json={"title": "B"}, headers=bob
        ).status_code
        == 404
    )
    assert (
        client.patch(
            f"/chats/{cid}", json={"title": "B"}, headers=alice
        ).json()["title"]
        == "B"
    )
    assert client.delete(f"/chats/{cid}", headers=bob).status_code == 404
    assert client.delete(f"/chats/{cid}", headers=alice).status_code == 204


def test_send_message_streams_and_persists(client):
    headers = _auth(client, "sender@x.ru")
    cid = client.post("/chats", json={}, headers=headers).json()["id"]
    with client.stream(
        "POST",
        f"/chats/{cid}/messages",
        json={"query": "вопрос", "model_id": "local"},
        headers=headers,
    ) as stream:
        assert stream.status_code == 200
        events = [
            json.loads(line[6:])
            for line in stream.iter_lines()
            if line.startswith("data:")
        ]
    assert "".join(e.get("token", "") for e in events) == "Ответ"
    assert events[-1]["done"] is True
    assert events[-1]["sources"][0]["chunk_id"] == "d_0"
    messages = client.get(f"/chats/{cid}/messages", headers=headers).json()
    assert [m["role"] for m in messages] == ["user", "assistant"]
    assert messages[1]["model_used"] == "local"
    assert messages[1]["sources"][0]["chunk_id"] == "d_0"


def test_models_endpoint(client):
    ids = [m["id"] for m in client.get("/models").json()]
    assert ids == ["deepseek-chat", "llama-70b", "claude-haiku", "local"]


def test_documents_flow(client):
    headers = _auth(client, "docs@x.ru")
    r = client.post(
        "/documents",
        json={"url": "https://example.com/a"},
        headers=headers,
    )
    # без запущенного воркера/redis job может не встать в очередь —
    # допустимы 201 (pending) или 503 (нет очереди)
    assert r.status_code in (201, 503), r.text
    if r.status_code == 503:
        return
    did = r.json()["id"]
    assert r.json()["status"] == "pending"
    assert client.get(f"/documents/{did}", headers=headers).status_code == 200
    assert len(client.get("/documents", headers=headers).json()) >= 1
    assert (
        client.post(
            "/documents/upload",
            files={"file": ("a.exe", b"x")},
            headers=headers,
        ).status_code
        == 400
    )
    assert (
        client.delete(f"/documents/{did}", headers=headers).status_code == 204
    )
