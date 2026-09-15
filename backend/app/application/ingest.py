"""Use-case ingestion: load -> chunk -> embed -> store.

Статусы документа (pending/processing/done/error) пишутся
в DocumentRepository на каждом шаге. Дедупликация — по хэшу
нормализованного markdown: неизменённый контент не переэмбеддится.
"""

from __future__ import annotations

import hashlib
import uuid

from app.adapters.loaders.factory import LoaderFactory
from app.domain.document import DocumentStatus
from app.ports.chunker import Chunker
from app.ports.embedding_provider import EmbeddingProvider
from app.ports.repositories import DocumentRepository
from app.ports.vector_store import VectorStoreRepository


def content_hash(markdown: str) -> str:
    return hashlib.sha256(markdown.encode("utf-8")).hexdigest()


class IngestDocumentUseCase:
    def __init__(
        self,
        documents: DocumentRepository,
        vectors: VectorStoreRepository,
        embeddings: EmbeddingProvider,
        chunker: Chunker,
        factory: LoaderFactory | None = None,
    ):
        self.documents = documents
        self.vectors = vectors
        self.embeddings = embeddings
        self.chunker = chunker
        self.factory = factory or LoaderFactory()

    async def execute(self, document_id: str, user_id: str) -> None:
        doc = await self.documents.get(document_id, user_id)
        if doc is None:
            raise ValueError(f"Document {document_id} not found")
        await self.documents.set_status(document_id, DocumentStatus.PROCESSING)
        try:
            loader = self.factory.get(doc.origin)
            loaded = await loader.load(doc.origin)
            digest = content_hash(loaded.markdown)
            if doc.content_hash == digest:
                # Контент не изменился — переэмбеддировать нечего.
                await self.documents.set_status(
                    document_id, DocumentStatus.DONE
                )
                return
            chunks = await self.chunker.chunk(
                loaded.markdown,
                document_id=document_id,
                title=loaded.title,
                url=doc.origin if doc.source_type.value != "file" else None,
            )
            texts = [c.content for c in chunks]
            vectors = await self.embeddings.embed_texts(texts)
            await self.vectors.add(chunks, vectors)
            doc.content_hash = digest
            await self.documents.set_status(document_id, DocumentStatus.DONE)
        except Exception as e:
            await self.documents.set_status(
                document_id, DocumentStatus.ERROR, error=str(e)
            )
            raise


def new_document_id() -> str:
    return uuid.uuid4().hex
