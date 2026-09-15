"""In-memory репозитории: default до пункта 12 (Postgres).

Используются как fallback в DI и в тестах без инфраструктуры.
"""

from __future__ import annotations

import uuid

from app.domain.chat import Chat, ChatMessage
from app.domain.document import Document, DocumentStatus
from app.domain.user import User


class InMemoryUserRepository:
    def __init__(self):
        self._by_id: dict[str, User] = {}
        self._by_email: dict[str, User] = {}

    async def create(self, email: str, hashed_password: str) -> User:
        if email in self._by_email:
            raise ValueError("Email already registered")
        user = User(
            id=uuid.uuid4().hex,
            email=email,
            hashed_password=hashed_password,
        )
        self._by_id[user.id] = user
        self._by_email[email] = user
        return user

    async def get_by_email(self, email: str) -> User | None:
        return self._by_email.get(email)

    async def get_by_id(self, user_id: str) -> User | None:
        return self._by_id.get(user_id)


class InMemoryChatRepository:
    def __init__(self):
        self._chats: dict[str, Chat] = {}
        self._messages: dict[str, list[ChatMessage]] = {}

    async def create_chat(self, user_id: str, title: str) -> Chat:
        chat = Chat(id=uuid.uuid4().hex, user_id=user_id, title=title)
        self._chats[chat.id] = chat
        self._messages[chat.id] = []
        return chat

    async def list_chats(self, user_id: str) -> list[Chat]:
        return [c for c in self._chats.values() if c.user_id == user_id]

    async def get_chat(self, chat_id: str, user_id: str) -> Chat | None:
        chat = self._chats.get(chat_id)
        if chat and chat.user_id == user_id:
            return chat
        return None

    async def rename_chat(
        self, chat_id: str, user_id: str, title: str
    ) -> Chat | None:
        chat = await self.get_chat(chat_id, user_id)
        if chat:
            chat.title = title
        return chat

    async def delete_chat(self, chat_id: str, user_id: str) -> bool:
        chat = await self.get_chat(chat_id, user_id)
        if not chat:
            return False
        del self._chats[chat_id]
        self._messages.pop(chat_id, None)
        return True

    async def add_message(self, message: ChatMessage) -> ChatMessage:
        self._messages.setdefault(message.chat_id, []).append(message)
        return message

    async def list_messages(
        self, chat_id: str, user_id: str, limit: int = 100
    ) -> list[ChatMessage]:
        chat = await self.get_chat(chat_id, user_id)
        if not chat:
            return []
        return self._messages.get(chat_id, [])[-limit:]


class InMemoryDocumentRepository:
    def __init__(self):
        self._docs: dict[str, Document] = {}

    async def create(self, document: Document) -> Document:
        self._docs[document.id] = document
        return document

    async def get(self, doc_id: str, user_id: str) -> Document | None:
        doc = self._docs.get(doc_id)
        if doc and doc.user_id == user_id:
            return doc
        return None

    async def list(self, user_id: str) -> list[Document]:
        return [d for d in self._docs.values() if d.user_id == user_id]

    async def set_status(
        self,
        doc_id: str,
        status: DocumentStatus,
        error: str | None = None,
    ) -> None:
        doc = self._docs.get(doc_id)
        if doc:
            doc.status = status
            doc.error = error

    async def set_hash(self, doc_id: str, digest: str) -> None:
        doc = self._docs.get(doc_id)
        if doc:
            doc.content_hash = digest

    async def delete(self, doc_id: str, user_id: str) -> bool:
        doc = await self.get(doc_id, user_id)
        if not doc:
            return False
        del self._docs[doc_id]
        return True
