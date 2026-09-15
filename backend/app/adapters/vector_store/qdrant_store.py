"""QdrantVectorStore: гибрид dense+sparse с RRF-фьюжном.

- Одна коллекция, именованные векторы: dense (bge-m3, 1024) + sparse.
- Payload: user_id/document_id/chunk_id/title/url/created_at,
  индексы на user_id и document_id.
- Фильтрация по user_id на каждый запрос (изоляция пользователей).
- Point id — детерминированный UUIDv5 от chunk.id (Qdrant принимает
  только UUID/uint, а chunk.id вида "doc_3" — произвольная строка).
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime

from app.domain.document import Chunk
from app.ports.vector_store import ScoredChunk

DENSE_NAME = "dense"
SPARSE_NAME = "sparse"
PREFETCH_LIMIT = 30


def point_id(chunk_id: str) -> str:
    """Детерминированный UUID точки Qdrant из chunk.id."""
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"rag-chunk:{chunk_id}"))


def chunk_payload(chunk: Chunk, user_id: str) -> dict:
    return {
        "user_id": user_id,
        "document_id": chunk.document_id,
        "chunk_id": chunk.id,
        "content": chunk.content,
        "title": chunk.title,
        "section": chunk.section,
        "url": chunk.url,
        "created_at": datetime.utcnow().isoformat(),
    }


def payload_to_chunk(payload: dict, content: str) -> Chunk:
    return Chunk(
        id=payload["chunk_id"],
        document_id=payload["document_id"],
        content=content,
        title=payload.get("title"),
        section=payload.get("section"),
        url=payload.get("url"),
    )


class QdrantVectorStore:
    """Адаптер VectorStoreRepository на Qdrant."""

    def __init__(
        self,
        url: str = "http://localhost:6333",
        collection: str = "collections_docs",
        dense_dim: int = 1024,
    ):
        self.url = url
        self.collection = collection
        self.dense_dim = dense_dim
        self._client = None
        self._sparse_model = None

    def _client_or_create(self):
        if self._client is None:
            from qdrant_client import QdrantClient

            self._client = QdrantClient(url=self.url)
        return self._client

    def _sparse_or_load(self):
        if self._sparse_model is None:
            from fastembed import SparseTextEmbedding

            self._sparse_model = SparseTextEmbedding("Qdrant/bm25")
        return self._sparse_model

    async def ensure_collection(self) -> None:
        await asyncio.to_thread(self._ensure_collection_sync)

    def _ensure_collection_sync(self) -> None:
        from qdrant_client.http import models

        client = self._client_or_create()
        try:
            client.get_collection(self.collection)
            return
        except Exception:
            pass
        client.create_collection(
            collection_name=self.collection,
            vectors_config={
                DENSE_NAME: models.VectorParams(
                    size=self.dense_dim,
                    distance=models.Distance.COSINE,
                )
            },
            sparse_vectors_config={SPARSE_NAME: models.SparseVectorParams()},
        )
        for key in ("user_id", "document_id"):
            client.create_payload_index(
                collection_name=self.collection,
                field_name=key,
                field_schema=models.PayloadSchemaType.KEYWORD,
            )

    async def add(
        self,
        chunks: list[Chunk],
        embeddings: list[list[float]],
        user_id: str = "",
    ) -> None:
        if not user_id:
            raise ValueError("user_id is required for payload isolation")
        points = await asyncio.to_thread(
            self._build_points, chunks, embeddings, user_id
        )
        client = self._client_or_create()
        await asyncio.to_thread(
            client.upsert, collection_name=self.collection, points=points
        )

    def _build_points(self, chunks, embeddings, user_id: str):
        from qdrant_client.http import models

        sparse_vecs = list(
            self._sparse_or_load().embed([c.content for c in chunks])
        )
        points = []
        for chunk, dense, sparse in zip(chunks, embeddings, sparse_vecs):
            points.append(
                models.PointStruct(
                    id=point_id(chunk.id),
                    vector={
                        DENSE_NAME: dense,
                        SPARSE_NAME: models.SparseVector(
                            indices=sparse.indices.tolist(),
                            values=sparse.values.tolist(),
                        ),
                    },
                    payload=chunk_payload(chunk, user_id),
                )
            )
        return points

    async def search(
        self,
        query: str,
        query_embedding: list[float],
        user_id: str,
        top_k: int = 5,
    ) -> list[ScoredChunk]:
        from qdrant_client.http import models

        client = self._client_or_create()
        sparse_vecs = await asyncio.to_thread(
            lambda: list(self._sparse_or_load().embed([query]))
        )
        sparse = sparse_vecs[0]
        result = await asyncio.to_thread(
            client.query_points,
            collection_name=self.collection,
            prefetch=[
                models.Prefetch(
                    query=query_embedding,
                    using=DENSE_NAME,
                    limit=PREFETCH_LIMIT,
                ),
                models.Prefetch(
                    query=models.SparseVector(
                        indices=sparse.indices.tolist(),
                        values=sparse.values.tolist(),
                    ),
                    using=SPARSE_NAME,
                    limit=PREFETCH_LIMIT,
                ),
            ],
            query=models.FusionQuery(fusion=models.Fusion.RRF),
            query_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="user_id",
                        match=models.MatchValue(value=user_id),
                    )
                ]
            ),
            limit=top_k,
            with_payload=True,
        )
        scored = []
        for pt in result.points:
            payload = pt.payload or {}
            scored.append(
                ScoredChunk(
                    chunk=payload_to_chunk(
                        payload, payload.get("content", "")
                    ),
                    score=pt.score,
                )
            )
        return scored

    async def delete_by_document(self, document_id: str) -> None:
        from qdrant_client.http import models

        client = self._client_or_create()
        await asyncio.to_thread(
            client.delete,
            collection_name=self.collection,
            points_selector=models.FilterSelector(
                filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="document_id",
                            match=models.MatchValue(value=document_id),
                        )
                    ]
                )
            ),
        )
