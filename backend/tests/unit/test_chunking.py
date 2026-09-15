"""Unit: маппинг Docling-чанка, сортировка реранкера, промпт."""

from app.adapters.chunkers.hybrid_chunker import dl_chunk_to_chunk
from app.adapters.reranker.bge_reranker import order_by_score
from app.application.chat import build_prompt
from app.domain.document import Chunk


class _Meta:
    def __init__(self, headings):
        self.headings = headings


class _DlChunk:
    def __init__(self, text, headings):
        self.text = text
        self.meta = _Meta(headings)


def test_dl_chunk_to_chunk_headings():
    chunk = dl_chunk_to_chunk(
        _DlChunk("  текст  ", ["Глава", "Раздел"]),
        "doc",
        2,
        url="https://x",
    )
    assert chunk.id == "doc_2"
    assert chunk.content == "текст"
    assert chunk.title == "Глава"
    assert chunk.section == "Глава / Раздел"
    assert chunk.url == "https://x"
    assert chunk.metadata == {"headings": ["Глава", "Раздел"]}


def test_dl_chunk_to_chunk_no_headings():
    chunk = dl_chunk_to_chunk(_DlChunk("t", []), "doc", 0)
    assert chunk.title is None and chunk.section is None


def test_order_by_score_top_k():
    chunks = [
        Chunk(id=f"c{i}", document_id="d", content="t") for i in range(4)
    ]
    ranked = order_by_score(chunks, [0.1, 0.9, 0.5, 0.3], top_k=2)
    assert [c.id for c, _ in ranked] == ["c1", "c2"]
    assert ranked[0][1] == 0.9


def test_build_prompt_substitutes_all_parts():
    prompt = build_prompt(
        "Q:{question} C:{context} H:{chat_history}",
        "вопрос?",
        ["чанк1", "чанк2"],
        [],
    )
    assert "вопрос?" in prompt
    assert "чанк1\n\n[DOC]\n\nчанк2" in prompt
