"""State models for Safari Reader."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

__all__ = [
    "BookMeta",
    "Bookmark",
    "ReaderSettings",
    "SafariReaderExitRequest",
    "SafariReaderState",
]


@dataclass(frozen=True)
class SafariReaderExitRequest:
    """Describe a handoff request emitted by the Safari Reader app."""

    action: str
    document_path: Path | None = None


@dataclass
class BookMeta:
    """Metadata for a book in the local library."""

    title: str = ""
    author: str = ""
    language: str = "en"
    source: str = ""
    source_id: str = ""
    subjects: list[str] = field(default_factory=list)
    file_path: Path | None = None
    format: str = "txt"
    size_bytes: int = 0
    added: str = ""
    last_opened: str = ""
    progress_percent: float = 0.0
    current_position: int = 0
    total_chars: int = 0
    reading_time_seconds: int = 0


@dataclass
class Bookmark:
    """A saved bookmark within a book."""

    name: str
    position: int
    chapter: str = ""
    excerpt: str = ""
    created: str = ""


@dataclass
class ReaderSettings:
    """Display and behaviour settings for the reader."""

    text_scale: int = 1  # 0=compact, 1=normal, 2=large, 3=xlarge
    line_spacing: int = 1  # 1=single, 2=one-and-half, 3=double
    margin_width: int = 1  # 0=narrow, 1=normal, 2=wide
    page_mode: bool = True  # True=page, False=flow/scroll
    justify: bool = False


@dataclass
class SafariReaderState:
    """Mutable state shared across Safari Reader screens."""

    library_dir: Path = field(default_factory=lambda: _default_library_dir())
    library: list[BookMeta] = field(default_factory=list)
    current_book: BookMeta | None = None
    current_text: str = ""
    current_chapters: list[tuple[str, int]] = field(default_factory=list)
    current_position: int = 0
    bookmarks: list[Bookmark] = field(default_factory=list)
    settings: ReaderSettings = field(default_factory=ReaderSettings)
    catalog_results: list[dict[str, str]] = field(default_factory=list)
    catalog_query: str = ""
    last_search: str = ""


def _default_library_dir() -> Path:
    """Return the default library directory, creating it if needed."""
    d = Path.home() / ".safari_reader" / "library"
    d.mkdir(parents=True, exist_ok=True)
    return d
