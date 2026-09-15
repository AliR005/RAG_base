"""Unit: IngestDocumentUseCase и RetrieveUseCase на фейках."""

import pytest
from app.application.ingest import IngestDocumentUseCase, content_hash
from app.application.retrieve import RetrieveUseCase
from app.domain.document import (
    Chunk,
    Document,
    DocumentStatus,
    SourceType,
)
from app.ports.document_loader import LoadedDocument
from app.ports.vector_store import ScoredChunk
from tests.conftest import run


class FakeDocRepo:
    def __init__(self, doc):
        self.doc = doc
        self.statuses = []

    async def create(self, document):
        return document

    async def get(self, doc_id, user_id):
        return self.doc

    async def list(self, user_id):
        return [self.doc]

    async def set_status(self, doc_id, status, error=None):
        self.doc.status = status
        self.doc.error = error
        self.statuses.append(status)

    async def set_hash(self, doc_id, digest):
        self.doc.content_hash = digest

    async def delete(self, doc_id, user_id):
        return True


class FakeVectors:
    def __init__(self):
        self.added = 0

    async def add(self, chunks, embeddings, user_id=""):
        self.added += len(chunks)

    async def search(self, query, embedding, user_id, top_k=5):
        return [
            ScoredChunk(
                chunk=Chunk(id="d_0", document_id="d", content="контекст"),
                score=0.9,
            )
        ][:top_k]

    async def delete_by_document(self, document_id):
        pass


class FakeEmb:
    async def embed_texts(self, texts):
        return [[0.1] for _ in texts]

    async def embed_query(self, query):
        return [0.1]


class FakeLoader:
    source_type = SourceType.FILE

    def __init__(self, markdown="# T\n\nтекст"):
        self.markdown = markdown
        self.calls = 0

    async def load(self, origin):
        self.calls += 1
        return LoadedDocument(markdown=self.markdown, title="T")


class FakeChunker:
    async def chunk(self, markdown, document_id, title=None, url=None):
        return [
            Chunk(
                id=f"{document_id}_0",
                document_id=document_id,
                content=markdown,
            )
        ]


class FakeFactory:
    def __init__(self, loader):
        self.loader = loader

    def get(self, origin):
        return self.loader


def _doc():
    return Document(
        id="d", user_id="u", source_type=SourceType.FILE, origin="/tmp/a.md"
    )


def test_ingest_success_sets_done_and_hash():
    doc, loader, vectors = _doc(), FakeLoader(), FakeVectors()
    uc = IngestDocumentUseCase(
        FakeDocRepo(doc),
        vectors,
        FakeEmb(),
        FakeChunker(),
        FakeFactory(loader),
    )
    run(uc.execute("d", "u"))
    assert doc.status == DocumentStatus.DONE
    assert doc.content_hash == content_hash(loader.markdown)
    assert vectors.added == 1


def test_ingest_dedup_skips_reembed():
    loader = FakeLoader()
    doc = _doc()
    doc.content_hash = content_hash(loader.markdown)
    vectors = FakeVectors()
    uc = IngestDocumentUseCase(
        FakeDocRepo(doc),
        vectors,
        FakeEmb(),
        FakeChunker(),
        FakeFactory(loader),
    )
    run(uc.execute("d", "u"))
    assert doc.status == DocumentStatus.DONE
    assert vectors.added == 0


def test_ingest_error_sets_error_status_and_reraises():
    class BrokenLoader(FakeLoader):
        async def load(self, origin):
            raise RuntimeError("boom")

    doc = _doc()
    uc = IngestDocumentUseCase(
        FakeDocRepo(doc),
        FakeVectors(),
        FakeEmb(),
        FakeChunker(),
        FakeFactory(BrokenLoader()),
    )
    with pytest.raises(RuntimeError):
        run(uc.execute("d", "u"))
    assert doc.status == DocumentStatus.ERROR
    assert doc.error == "boom"


def test_retrieve_uses_reranker_and_candidate_limit():
    seen = {}

    class Store(FakeVectors):
        async def search(self, query, embedding, user_id, top_k=5):
            seen["top_k"] = top_k
            return [
                ScoredChunk(
                    chunk=Chunk(id=f"c{i}", document_id="d", content=f"t{i}"),
                    score=0.1 * i,
                )
                for i in range(3)
            ]

    class Reranker:
        async def rerank(self, query, chunks, top_k=5):
            return [(chunks[2], 0.99), (chunks[0], 0.5)][:top_k]

    uc = RetrieveUseCase(Store(), FakeEmb(), Reranker())
    out = run(uc.execute("q", "u", top_k=2))
    assert seen["top_k"] == 30
    assert [s.chunk.id for s in out] == ["c2", "c0"]


def test_retrieve_without_reranker_passthrough():
    uc = RetrieveUseCase(FakeVectors(), FakeEmb(), None)
    out = run(uc.execute("q", "u", top_k=5))
    assert len(out) == 1 and out[0].chunk.id == "d_0"
