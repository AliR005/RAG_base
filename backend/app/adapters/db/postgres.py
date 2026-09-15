"""Postgres-репозитории (async SQLAlchemy) под порты."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import asdict

from app.adapters.db.models import (
    ChatRow,
    DocumentRow,
    MessageRow,
    UserRow,
    new_id,
)
from app.domain.chat import Chat, ChatMessage, Citation
from app.domain.document import Document, DocumentStatus, SourceType
from app.domain.user import User
from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


def _citation_to_dict(c: Citation) -> dict:
    return asdict(c)


def _citation_from_dict(d: dict) -> Citation:
    return Citation(
        chunk_id=d["chunk_id"],
        document_id=d["document_id"],
        title=d.get("title"),
        url=d.get("url"),
        snippet=d.get("snippet"),
    )


class PostgresUserRepository:
    def __init__(self, sessions: async_sessionmaker[AsyncSession]):
        self.sessions = sessions

    async def create(self, email: str, hashed_password: str) -> User:
        async with self.sessions() as s:
            row = UserRow(
                id=new_id(), email=email, hashed_password=hashed_password
            )
            s.add(row)
            await s.commit()
            return User(
                id=row.id,
                email=row.email,
                hashed_password=row.hashed_password,
                created_at=row.created_at,
            )

    async def get_by_email(self, email: str) -> User | None:
        async with self.sessions() as s:
            row = (
                await s.execute(select(UserRow).where(UserRow.email == email))
            ).scalar_one_or_none()
            return _user(row) if row else None

    async def get_by_id(self, user_id: str) -> User | None:
        async with self.sessions() as s:
            row = await s.get(UserRow, user_id)
            return _user(row) if row else None


def _user(row: UserRow) -> User:
    return User(
        id=row.id,
        email=row.email,
        hashed_password=row.hashed_password,
        created_at=row.created_at,
    )


class PostgresChatRepository:
    def __init__(self, sessions: async_sessionmaker[AsyncSession]):
        self.sessions = sessions

    async def create_chat(self, user_id: str, title: str) -> Chat:
        async with self.sessions() as s:
            row = ChatRow(id=new_id(), user_id=user_id, title=title)
            s.add(row)
            await s.commit()
            return _chat(row)

    async def list_chats(self, user_id: str) -> list[Chat]:
        async with self.sessions() as s:
            rows = (
                await s.execute(
                    select(ChatRow)
                    .where(ChatRow.user_id == user_id)
                    .order_by(ChatRow.updated_at.desc())
                )
            ).scalars()
            return [_chat(r) for r in rows]

    async def get_chat(self, chat_id: str, user_id: str) -> Chat | None:
        async with self.sessions() as s:
            row = await s.get(ChatRow, chat_id)
            if row and row.user_id == user_id:
                return _chat(row)
            return None

    async def rename_chat(
        self, chat_id: str, user_id: str, title: str
    ) -> Chat | None:
        async with self.sessions() as s:
            row = await s.get(ChatRow, chat_id)
            if not row or row.user_id != user_id:
                return None
            row.title = title
            await s.commit()
            return _chat(row)

    async def delete_chat(self, chat_id: str, user_id: str) -> bool:
        async with self.sessions() as s:
            row = await s.get(ChatRow, chat_id)
            if not row or row.user_id != user_id:
                return False
            await s.delete(row)
            await s.commit()
            return True

    async def add_message(self, message: ChatMessage) -> ChatMessage:
        async with self.sessions() as s:
            row = MessageRow(
                id=message.id or new_id(),
                chat_id=message.chat_id,
                role=message.role,
                content=message.content,
                model_used=message.model_used,
                sources_json=[_citation_to_dict(c) for c in message.sources],
            )
            s.add(row)
            await s.commit()
            message.id = row.id
            return message

    async def list_messages(
        self, chat_id: str, user_id: str, limit: int = 100
    ) -> list[ChatMessage]:
        async with self.sessions() as s:
            chat = await s.get(ChatRow, chat_id)
            if not chat or chat.user_id != user_id:
                return []
            rows = (
                await s.execute(
                    select(MessageRow)
                    .where(MessageRow.chat_id == chat_id)
                    .order_by(MessageRow.created_at.asc())
                    .limit(limit)
                )
            ).scalars()
            return [_message(r) for r in rows]


def _chat(row: ChatRow) -> Chat:
    return Chat(
        id=row.id,
        user_id=row.user_id,
        title=row.title,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _message(row: MessageRow) -> ChatMessage:
    return ChatMessage(
        id=row.id,
        chat_id=row.chat_id,
        role=row.role,
        content=row.content,
        model_used=row.model_used,
        sources=[_citation_from_dict(d) for d in row.sources_json or []],
        created_at=row.created_at,
    )


class PostgresDocumentRepository:
    def __init__(self, sessions: async_sessionmaker[AsyncSession]):
        self.sessions = sessions

    async def create(self, document: Document) -> Document:
        async with self.sessions() as s:
            row = DocumentRow(
                id=document.id or new_id(),
                user_id=document.user_id,
                source_type=document.source_type.value,
                origin=document.origin,
                title=document.title,
                status=document.status.value,
                content_hash=document.content_hash,
                error=document.error,
            )
            s.add(row)
            await s.commit()
            document.id = row.id
            return document

    async def get(self, doc_id: str, user_id: str) -> Document | None:
        async with self.sessions() as s:
            row = await s.get(DocumentRow, doc_id)
            if row and row.user_id == user_id:
                return _document(row)
            return None

    async def list(self, user_id: str) -> list[Document]:
        async with self.sessions() as s:
            rows = (
                await s.execute(
                    select(DocumentRow).where(DocumentRow.user_id == user_id)
                )
            ).scalars()
            return [_document(r) for r in rows]

    async def set_status(
        self,
        doc_id: str,
        status: DocumentStatus,
        error: str | None = None,
    ) -> None:
        async with self.sessions() as s:
            row = await s.get(DocumentRow, doc_id)
            if row:
                row.status = status.value
                row.error = error
                await s.commit()

    async def delete(self, doc_id: str, user_id: str) -> bool:
        async with self.sessions() as s:
            row = await s.get(DocumentRow, doc_id)
            if not row or row.user_id != user_id:
                return False
            await s.delete(row)
            await s.commit()
            return True

    async def set_hash(self, doc_id: str, digest: str) -> None:
        async with self.sessions() as s:
            row = await s.get(DocumentRow, doc_id)
            if row:
                row.content_hash = digest
                await s.commit()


def _document(row: DocumentRow) -> Document:
    return Document(
        id=row.id,
        user_id=row.user_id,
        source_type=SourceType(row.source_type),
        origin=row.origin,
        status=DocumentStatus(row.status),
        title=row.title,
        content_hash=row.content_hash,
        error=row.error,
        created_at=row.created_at,
    )


def make_session_factory(database_url: str):
    engine = create_async_engine(database_url, pool_pre_ping=True)
    return async_sessionmaker(engine, expire_on_commit=False)


@asynccontextmanager
async def session_scope(
    sessions: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncSession]:
    async with sessions() as session:
        yield session
