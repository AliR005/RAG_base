"""Документы: загрузка (файл/URL/YouTube), статусы, удаление.

Единая точка входа: файл (multipart) или {"url": ...}. Ingestion идёт
через очередь arq, статус виден через GET (поллинг).
"""

from __future__ import annotations

from pathlib import Path

from app.adapters.loaders.factory import detect_source_type
from app.application.ingest import new_document_id
from app.core.config import BASE_DIR, settings
from app.core.dependencies import (
    get_document_repository,
    get_qdrant_store,
)
from app.domain.document import Document
from app.domain.user import User
from app.ports.repositories import DocumentRepository
from app.ports.vector_store import VectorStoreRepository
from app.routers.auth import get_current_user
from app.schemas.documents import DocumentCreate, DocumentOut
from app.worker import enqueue_ingest
from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
)

router = APIRouter(prefix="/documents", tags=["documents"])

UPLOAD_DIR = BASE_DIR / "uploads"


def _out(doc: Document) -> DocumentOut:
    return DocumentOut(
        id=doc.id,
        source_type=doc.source_type.value,
        origin=doc.origin,
        title=doc.title,
        status=doc.status.value,
        error=doc.error,
        created_at=doc.created_at,
    )


async def _enqueue_or_fail(doc_id: str, user_id: str) -> None:
    try:
        await enqueue_ingest(settings.REDIS_URL, doc_id, user_id)
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Queue unavailable: {e}",
        ) from e


@router.post("", response_model=DocumentOut, status_code=201)
async def create_from_url(
    body: DocumentCreate,
    user: User = Depends(get_current_user),
    docs: DocumentRepository = Depends(get_document_repository),
) -> DocumentOut:
    source = detect_source_type(body.url)
    doc = await docs.create(
        Document(
            id=new_document_id(),
            user_id=user.id,
            source_type=source,
            origin=body.url,
        )
    )
    await _enqueue_or_fail(doc.id, user.id)
    created = await docs.get(doc.id, user.id)
    assert created is not None
    return _out(created)


@router.post("/upload", response_model=DocumentOut, status_code=201)
async def upload_file(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    docs: DocumentRepository = Depends(get_document_repository),
) -> DocumentOut:
    from app.adapters.loaders.docling_loader import SUPPORTED_SUFFIXES

    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in SUPPORTED_SUFFIXES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {suffix!r}",
        )
    doc_id = new_document_id()
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    dest = UPLOAD_DIR / f"{doc_id}{suffix}"
    content = await file.read()
    dest.write_bytes(content)
    doc = await docs.create(
        Document(
            id=doc_id,
            user_id=user.id,
            source_type=detect_source_type(str(dest)),
            origin=str(dest),
        )
    )
    await _enqueue_or_fail(doc.id, user.id)
    created = await docs.get(doc.id, user.id)
    assert created is not None
    return _out(created)


@router.get("", response_model=list[DocumentOut])
async def list_documents(
    user: User = Depends(get_current_user),
    docs: DocumentRepository = Depends(get_document_repository),
) -> list[DocumentOut]:
    return [_out(d) for d in await docs.list(user.id)]


@router.get("/{doc_id}", response_model=DocumentOut)
async def get_document(
    doc_id: str,
    user: User = Depends(get_current_user),
    docs: DocumentRepository = Depends(get_document_repository),
) -> DocumentOut:
    doc = await docs.get(doc_id, user.id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return _out(doc)


@router.delete("/{doc_id}", status_code=204)
async def delete_document(
    doc_id: str,
    user: User = Depends(get_current_user),
    docs: DocumentRepository = Depends(get_document_repository),
    vectors: VectorStoreRepository = Depends(get_qdrant_store),
):
    from fastapi import Response

    doc = await docs.get(doc_id, user.id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")
    await vectors.delete_by_document(doc_id)
    await docs.delete(doc_id, user.id)
    return Response(status_code=204)
