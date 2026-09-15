"""Unit: доменные сущности."""

from app.domain.chat import Chat, ChatMessage, Citation
from app.domain.document import (
    Chunk,
    Document,
    DocumentStatus,
    SourceType,
)
from app.domain.user import User


def test_document_defaults():
    doc = Document(
        id="d", user_id="u", source_type=SourceType.URL, origin="https://x"
    )
    assert doc.status == DocumentStatus.PENDING
    assert doc.content_hash is None
    assert doc.error is None


def test_chunk_metadata_defaults():
    chunk = Chunk(id="d_0", document_id="d", content="text")
    assert chunk.ordinal == 0
    assert chunk.metadata == {}


def test_chat_message_sources_default_empty():
    msg = ChatMessage(id="m", chat_id="c", role="user", content="hi")
    assert msg.sources == []
    assert msg.model_used is None


def test_citation_fields():
    cite = Citation(chunk_id="d_0", document_id="d", snippet="s")
    assert cite.title is None and cite.url is None


def test_user_fields():
    user = User(id="u", email="a@x.ru", hashed_password="h")
    assert user.email == "a@x.ru"


def test_chat_title_default():
    assert Chat(id="c", user_id="u").title == "Новый чат"
