"""YouTubeLoader: видео -> markdown с таймкодами.

Приоритет: субтитры через youtube-transcript-api. Если субтитров
нет — fallback: скачивание аудио через yt-dlp + транскрипция
faster-whisper. Тяжёлые импорты ленивые.
"""

from __future__ import annotations

import asyncio
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path

from app.domain.document import SourceType
from app.ports.document_loader import LoadedDocument

YOUTUBE_RE = re.compile(
    r"(?:youtube\.com/(?:watch\?v=|shorts/|embed/|live/)|youtu\.be/)"
    r"([\w-]{11})"
)

TRANSCRIPT_LANGS = ("ru", "en")


def is_youtube_url(origin: str) -> bool:
    return YOUTUBE_RE.search(origin) is not None


def extract_video_id(origin: str) -> str:
    match = YOUTUBE_RE.search(origin)
    if not match:
        raise ValueError(f"Not a YouTube URL: {origin!r}")
    return match.group(1)


@dataclass
class Segment:
    start: float  # секунды
    text: str


def format_timestamp(seconds: float) -> str:
    total = int(seconds)
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def build_markdown(
    title: str, video_id: str, segments: list[Segment]
) -> LoadedDocument:
    """Чистая функция: сегменты -> markdown с таймкодами."""
    lines = [f"# {title}", ""]
    for seg in segments:
        lines.append(f"## {format_timestamp(seg.start)}")
        lines.append(seg.text.strip())
        lines.append("")
    return LoadedDocument(
        markdown="\n".join(lines).strip() + "\n",
        title=title,
        source_type=SourceType.YOUTUBE,
        metadata={
            "video_id": video_id,
            "segments": [{"start": s.start, "text": s.text} for s in segments],
        },
    )


class YouTubeLoader:
    """Адаптер DocumentLoader для YouTube-видео."""

    source_type = SourceType.YOUTUBE

    def __init__(
        self,
        langs: tuple[str, ...] = TRANSCRIPT_LANGS,
        whisper_model: str = "base",
    ):
        self.langs = langs
        self.whisper_model = whisper_model

    async def load(self, origin: str) -> LoadedDocument:
        video_id = extract_video_id(origin)
        title = await asyncio.to_thread(self._fetch_title, origin)
        segments = await asyncio.to_thread(self._fetch_transcript, video_id)
        if segments is None:
            segments = await asyncio.to_thread(self._transcribe_audio, origin)
        return build_markdown(title, video_id, segments)

    def _fetch_title(self, origin: str) -> str:
        import yt_dlp

        with yt_dlp.YoutubeDL({"quiet": True, "skip_download": True}) as ydl:
            info = ydl.extract_info(origin, download=False)
        return info.get("title") or origin

    def _fetch_transcript(self, video_id: str) -> list[Segment] | None:
        """Субтитры. None — нет субтитров, нужен fallback."""
        try:
            from youtube_transcript_api import YouTubeTranscriptApi
        except ImportError as e:
            raise RuntimeError(
                "youtube-transcript-api is not installed"
            ) from e
        try:
            api = YouTubeTranscriptApi()
            if hasattr(api, "fetch"):
                fetched = api.fetch(video_id, languages=list(self.langs))
                items = fetched.snippets
                get = lambda s: (s.start, s.text)  # noqa: E731
            else:  # старый API <1.0
                items = api.get_transcript(
                    video_id, languages=list(self.langs)
                )
                get = lambda s: (s["start"], s["text"])  # noqa: E731
        except Exception:
            return None
        segments = [
            Segment(start=float(st), text=tx)
            for st, tx in (get(s) for s in items)
            if tx and tx.strip()
        ]
        return segments or None

    def _transcribe_audio(self, origin: str) -> list[Segment]:
        """Fallback: аудио через yt-dlp + faster-whisper."""
        try:
            from faster_whisper import WhisperModel
        except ImportError as e:
            raise RuntimeError(
                "No subtitles found and faster-whisper is not "
                "installed — cannot transcribe audio"
            ) from e
        import yt_dlp

        with tempfile.TemporaryDirectory() as tmp:
            outtmpl = str(Path(tmp) / "%(id)s.%(ext)s")
            with yt_dlp.YoutubeDL(
                {
                    "quiet": True,
                    "format": "bestaudio/best",
                    "outtmpl": outtmpl,
                    "noplaylist": True,
                }
            ) as ydl:
                info = ydl.extract_info(origin, download=True)
                audio_path = ydl.prepare_filename(info)
            model = WhisperModel(
                self.whisper_model, device="cpu", compute_type="int8"
            )
            raw_segments, _ = model.transcribe(audio_path)
            return [
                Segment(start=s.start, text=s.text)
                for s in raw_segments
                if s.text and s.text.strip()
            ]
