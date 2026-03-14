"""Library management, catalog search, and download services for Safari Reader."""

from __future__ import annotations

import json
import re
import textwrap
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

import httpx

from safari_reader.state import Bookmark, BookMeta, SafariReaderState

__all__ = [
    "add_book_to_library",
    "delete_book",
    "download_gutenberg_text",
    "format_book_text",
    "gutenberg_book_detail",
    "import_local_file",
    "load_library",
    "load_reading_state",
    "parse_chapters",
    "save_library",
    "save_reading_state",
    "search_gutenberg",
    "strip_html_tags",
    "top_gutenberg",
]

GUTENBERG_API = "https://gutendex.com/books"
GUTENBERG_MIRROR = "https://www.gutenberg.org"

# ── HTML stripping ────────────────────────────────────────────────


class _TagStripper(HTMLParser):
    """Minimal HTML→plain-text converter."""

    def __init__(self) -> None:
        super().__init__()
        self._parts: list[str] = []
        self._skip = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style"}:
            self._skip = True
        if tag in {"br", "p", "div", "h1", "h2", "h3", "h4", "h5", "h6", "li"}:
            self._parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style"}:
            self._skip = False
        if tag in {"p", "div", "h1", "h2", "h3", "h4", "h5", "h6"}:
            self._parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self._skip:
            self._parts.append(data)

    def get_text(self) -> str:
        return "".join(self._parts)


def strip_html_tags(html: str) -> str:
    """Convert HTML to plain text."""
    s = _TagStripper()
    s.feed(html)
    return s.get_text()


# ── Gutenberg API ────────────────────────────────────────────────


def search_gutenberg(
    query: str,
    *,
    search_field: str = "title",
    page: int = 1,
) -> list[dict[str, str]]:
    """Search the Gutendex API. Returns simplified result dicts."""
    params: dict[str, str | int] = {"page": page}
    if search_field == "title":
        params["search"] = query
    elif search_field == "author":
        params["search"] = query
    elif search_field == "topic":
        params["topic"] = query
    else:
        params["search"] = query

    try:
        resp = httpx.get(
            GUTENBERG_API, params=params, timeout=15, follow_redirects=True
        )
        resp.raise_for_status()
    except httpx.HTTPError:
        return []

    data = resp.json()
    results: list[dict[str, str]] = []
    for book in data.get("results", []):
        authors = ", ".join(a.get("name", "") for a in book.get("authors", []))
        subjects = "; ".join(book.get("subjects", [])[:3])
        results.append(
            {
                "id": str(book.get("id", "")),
                "title": book.get("title", "Untitled"),
                "author": authors,
                "language": ", ".join(book.get("languages", [])),
                "subjects": subjects,
                "download_count": str(book.get("download_count", 0)),
            }
        )
    return results


def top_gutenberg(*, page: int = 1) -> list[dict[str, str]]:
    """Fetch popular Gutenberg books sorted by download count."""
    params: dict[str, str | int] = {"page": page, "sort": "popular"}
    try:
        resp = httpx.get(
            GUTENBERG_API, params=params, timeout=15, follow_redirects=True
        )
        resp.raise_for_status()
    except httpx.HTTPError:
        return []

    data = resp.json()
    results: list[dict[str, str]] = []
    for book in data.get("results", []):
        authors = ", ".join(a.get("name", "") for a in book.get("authors", []))
        subjects = "; ".join(book.get("subjects", [])[:3])
        results.append(
            {
                "id": str(book.get("id", "")),
                "title": book.get("title", "Untitled"),
                "author": authors,
                "language": ", ".join(book.get("languages", [])),
                "subjects": subjects,
                "download_count": str(book.get("download_count", 0)),
            }
        )
    return results


def gutenberg_book_detail(book_id: str) -> dict[str, str]:
    """Fetch detailed metadata for a single Gutenberg book."""
    try:
        resp = httpx.get(
            f"{GUTENBERG_API}/{book_id}", timeout=15, follow_redirects=True
        )
        resp.raise_for_status()
    except httpx.HTTPError:
        return {}

    book = resp.json()
    authors = ", ".join(a.get("name", "") for a in book.get("authors", []))
    subjects = "; ".join(book.get("subjects", []))
    formats = book.get("formats", {})
    txt_url = ""
    for key, url in formats.items():
        if "text/plain" in key and "utf-8" in key.lower():
            txt_url = url
            break
    if not txt_url:
        for key, url in formats.items():
            if "text/plain" in key:
                txt_url = url
                break
    return {
        "id": str(book.get("id", "")),
        "title": book.get("title", "Untitled"),
        "author": authors,
        "language": ", ".join(book.get("languages", [])),
        "subjects": subjects,
        "download_count": str(book.get("download_count", 0)),
        "txt_url": txt_url,
    }


def download_gutenberg_text(book_id: str, dest_dir: Path) -> Path | None:
    """Download the plain-text version of a Gutenberg book to *dest_dir*."""
    detail = gutenberg_book_detail(book_id)
    if not detail or not detail.get("txt_url"):
        return None

    try:
        resp = httpx.get(detail["txt_url"], timeout=60, follow_redirects=True)
        resp.raise_for_status()
    except httpx.HTTPError:
        return None

    slug = re.sub(r"[^\w]+", "_", detail.get("title", book_id).lower()).strip("_")
    filename = f"pg{book_id}_{slug[:60]}.txt"
    dest_dir.mkdir(parents=True, exist_ok=True)
    path = dest_dir / filename
    path.write_text(resp.text, encoding="utf-8")
    return path


# ── Local library persistence ────────────────────────────────────


def _library_index_path(library_dir: Path) -> Path:
    return library_dir / "_index.json"


def _reading_state_path(library_dir: Path) -> Path:
    return library_dir / "_reading.json"


def save_library(state: SafariReaderState) -> None:
    """Persist the library index to disk."""
    data = []
    for b in state.library:
        data.append(
            {
                "title": b.title,
                "author": b.author,
                "language": b.language,
                "source": b.source,
                "source_id": b.source_id,
                "subjects": b.subjects,
                "file_path": str(b.file_path) if b.file_path else "",
                "format": b.format,
                "size_bytes": b.size_bytes,
                "added": b.added,
                "last_opened": b.last_opened,
                "progress_percent": b.progress_percent,
                "current_position": b.current_position,
                "total_chars": b.total_chars,
                "reading_time_seconds": b.reading_time_seconds,
            }
        )
    path = _library_index_path(state.library_dir)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def load_library(state: SafariReaderState) -> None:
    """Load the library index from disk into *state*."""
    path = _library_index_path(state.library_dir)
    if not path.exists():
        state.library = []
        return
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        state.library = []
        return
    books: list[BookMeta] = []
    for entry in data:
        fp = entry.get("file_path", "")
        books.append(
            BookMeta(
                title=entry.get("title", ""),
                author=entry.get("author", ""),
                language=entry.get("language", "en"),
                source=entry.get("source", ""),
                source_id=entry.get("source_id", ""),
                subjects=entry.get("subjects", []),
                file_path=Path(fp) if fp else None,
                format=entry.get("format", "txt"),
                size_bytes=entry.get("size_bytes", 0),
                added=entry.get("added", ""),
                last_opened=entry.get("last_opened", ""),
                progress_percent=entry.get("progress_percent", 0.0),
                current_position=entry.get("current_position", 0),
                total_chars=entry.get("total_chars", 0),
                reading_time_seconds=entry.get("reading_time_seconds", 0),
            )
        )
    state.library = books


def save_reading_state(state: SafariReaderState) -> None:
    """Persist bookmarks and current position for the active book."""
    if state.current_book is None:
        return
    book = state.current_book
    data = {
        "current_position": state.current_position,
        "bookmarks": [
            {
                "name": bm.name,
                "position": bm.position,
                "chapter": bm.chapter,
                "excerpt": bm.excerpt,
                "created": bm.created,
            }
            for bm in state.bookmarks
        ],
    }
    reading_path = _reading_state_path(state.library_dir)
    all_data: dict[str, dict] = {}
    if reading_path.exists():
        try:
            all_data = json.loads(reading_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            all_data = {}
    key = book.source_id or (str(book.file_path) if book.file_path else book.title)
    all_data[key] = data
    reading_path.write_text(json.dumps(all_data, indent=2), encoding="utf-8")


def load_reading_state(state: SafariReaderState) -> None:
    """Restore bookmarks and current position for the active book."""
    if state.current_book is None:
        return
    book = state.current_book
    reading_path = _reading_state_path(state.library_dir)
    if not reading_path.exists():
        return
    try:
        all_data = json.loads(reading_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return
    key = book.source_id or (str(book.file_path) if book.file_path else book.title)
    data = all_data.get(key)
    if not data:
        return
    state.current_position = data.get("current_position", 0)
    state.bookmarks = [
        Bookmark(
            name=bm.get("name", ""),
            position=bm.get("position", 0),
            chapter=bm.get("chapter", ""),
            excerpt=bm.get("excerpt", ""),
            created=bm.get("created", ""),
        )
        for bm in data.get("bookmarks", [])
    ]


# ── Book import and preparation ──────────────────────────────────


def import_local_file(path: Path, state: SafariReaderState) -> BookMeta:
    """Import a local file into the library."""
    path = path.expanduser().resolve()
    text = path.read_text(encoding="utf-8", errors="replace")
    suffix = path.suffix.lower()
    if suffix in {".html", ".htm"}:
        text = strip_html_tags(text)
    state.library_dir.mkdir(parents=True, exist_ok=True)
    existing = next(
        (
            book
            for book in state.library
            if book.source == "local" and book.source_id == str(path)
        ),
        None,
    )
    if existing is not None and existing.file_path is not None:
        dest = existing.file_path
    else:
        dest = _unique_library_path(state.library_dir, path.name)
    dest.write_text(text, encoding="utf-8")
    now = datetime.now(tz=timezone.utc).isoformat()
    if existing is not None:
        existing.title = path.stem.replace("_", " ").replace("-", " ").title()
        existing.file_path = dest
        existing.format = suffix.lstrip(".") or "txt"
        existing.size_bytes = len(text.encode("utf-8"))
        existing.total_chars = len(text)
        meta = existing
    else:
        meta = BookMeta(
            title=path.stem.replace("_", " ").replace("-", " ").title(),
            file_path=dest,
            format=suffix.lstrip(".") or "txt",
            size_bytes=len(text.encode("utf-8")),
            added=now,
            total_chars=len(text),
            source="local",
            source_id=str(path),
        )
        state.library.append(meta)
    save_library(state)
    return meta


def _unique_library_path(library_dir: Path, filename: str) -> Path:
    """Return a non-conflicting destination path inside the library."""
    candidate = library_dir / filename
    if not candidate.exists():
        return candidate
    stem = candidate.stem
    suffix = candidate.suffix
    counter = 2
    while True:
        candidate = library_dir / f"{stem}_{counter}{suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def add_book_to_library(
    detail: dict[str, str],
    file_path: Path,
    state: SafariReaderState,
) -> BookMeta:
    """Register a downloaded file in the library."""
    text = file_path.read_text(encoding="utf-8", errors="replace")
    now = datetime.now(tz=timezone.utc).isoformat()
    meta = BookMeta(
        title=detail.get("title", file_path.stem),
        author=detail.get("author", ""),
        language=detail.get("language", "en"),
        source="gutenberg",
        source_id=detail.get("id", ""),
        subjects=[
            s.strip() for s in detail.get("subjects", "").split(";") if s.strip()
        ],
        file_path=file_path,
        format="txt",
        size_bytes=len(text.encode("utf-8")),
        added=now,
        total_chars=len(text),
    )
    state.library.append(meta)
    save_library(state)
    return meta


def delete_book(book: BookMeta, state: SafariReaderState) -> None:
    """Remove a book from the library and delete its file."""
    if book.file_path and book.file_path.exists():
        book.file_path.unlink(missing_ok=True)
    if book in state.library:
        state.library.remove(book)
    save_library(state)


def open_book(book: BookMeta, state: SafariReaderState) -> None:
    """Load a book's text and prepare it for reading."""
    if book.file_path is None or not book.file_path.exists():
        state.current_text = ""
        state.current_chapters = []
        return
    text = book.file_path.read_text(encoding="utf-8", errors="replace")
    state.current_book = book
    state.current_text = text
    state.current_chapters = parse_chapters(text)
    book.total_chars = len(text)
    book.last_opened = datetime.now(tz=timezone.utc).isoformat()
    load_reading_state(state)
    save_library(state)


def parse_chapters(text: str) -> list[tuple[str, int]]:
    """Extract chapter headings and their character offsets."""
    chapters: list[tuple[str, int]] = []
    pattern = re.compile(
        r"^(CHAPTER|Chapter|BOOK|PART|SECTION|ACT|SCENE)" r"[\s.:]+(.*)$",
        re.MULTILINE,
    )
    for m in pattern.finditer(text):
        label = m.group(0).strip()[:60]
        chapters.append((label, m.start()))
    if not chapters:
        chapters.append(("Beginning", 0))
    return chapters


def format_book_text(
    text: str,
    width: int = 72,
    margin: int = 4,
) -> str:
    """Rewrap text for display at the given width with margins."""
    effective = max(20, width - margin * 2)
    paragraphs = re.split(r"\n\s*\n", text)
    margin_str = " " * margin
    out: list[str] = []
    for para in paragraphs:
        para = para.strip()
        if not para:
            out.append("")
            continue
        lines = textwrap.wrap(para, width=effective)
        for line in lines:
            out.append(margin_str + line)
        out.append("")
    return "\n".join(out)
