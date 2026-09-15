"""Unit: роутинг LoaderFactory и YouTube-хелперы."""

import pytest
from app.adapters.loaders.docling_loader import DoclingLoader
from app.adapters.loaders.factory import LoaderFactory, detect_source_type
from app.adapters.loaders.youtube_loader import (
    Segment,
    YouTubeLoader,
    build_markdown,
    extract_video_id,
    format_timestamp,
    is_youtube_url,
)
from app.domain.document import SourceType


@pytest.mark.parametrize(
    "origin,expected",
    [
        ("https://www.youtube.com/watch?v=dQw4w9WgXcQ", SourceType.YOUTUBE),
        ("https://youtu.be/dQw4w9WgXcQ", SourceType.YOUTUBE),
        ("https://www.youtube.com/shorts/dQw4w9WgXcQ", SourceType.YOUTUBE),
        ("https://example.com/article", SourceType.URL),
        ("http://localhost/file.pdf", SourceType.URL),
        ("/data/docs/file.pdf", SourceType.FILE),
        ("relative/path.docx", SourceType.FILE),
    ],
)
def test_detect_source_type(origin, expected):
    assert detect_source_type(origin) == expected


def test_factory_routes_youtube_to_youtube_loader():
    factory = LoaderFactory()
    assert isinstance(
        factory.get("https://youtu.be/dQw4w9WgXcQ"), YouTubeLoader
    )


@pytest.mark.parametrize(
    "origin",
    ["https://example.com/a", "/tmp/a.pdf", "doc.md"],
)
def test_factory_routes_other_to_docling(origin):
    factory = LoaderFactory()
    assert isinstance(factory.get(origin), DoclingLoader)


def test_youtube_url_detection():
    assert is_youtube_url("https://youtu.be/dQw4w9WgXcQ")
    assert not is_youtube_url("https://example.com/")


def test_extract_video_id():
    assert extract_video_id("https://youtu.be/dQw4w9WgXcQ") == "dQw4w9WgXcQ"
    with pytest.raises(ValueError):
        extract_video_id("https://example.com/")


def test_format_timestamp():
    assert format_timestamp(0) == "00:00"
    assert format_timestamp(65) == "01:05"
    assert format_timestamp(3725) == "01:02:05"


def test_build_markdown_timestamps_and_metadata():
    doc = build_markdown(
        "Тест",
        "vid1",
        [Segment(0.0, "привет"), Segment(65.5, "мир")],
    )
    assert doc.title == "Тест"
    assert "## 00:00" in doc.markdown
    assert "## 01:05" in doc.markdown
    assert doc.metadata["video_id"] == "vid1"
    assert len(doc.metadata["segments"]) == 2
