"""Reusable document file helpers."""

from __future__ import annotations

from importlib.resources import files
from pathlib import Path

from safari_writer.format_codec import decode_sfw, encode_sfw, is_sfw, strip_controls
from safari_writer.state import AppState

DEMO_DOCUMENT_RESOURCE = "demo_document.sfw"

__all__ = [
    "DEMO_DOCUMENT_RESOURCE",
    "load_demo_document_buffer",
    "load_document_buffer",
    "load_document_state",
    "serialize_document_buffer",
]


def load_document_buffer(path: Path, encoding: str = "utf-8") -> list[str]:
    """Load a document file into Safari Writer's in-memory buffer format."""

    text = path.read_text(encoding=encoding, errors="replace")
    if is_sfw(path.name):
        return decode_sfw(text)
    return text.split("\n") if text else [""]


def load_demo_document_buffer(encoding: str = "utf-8") -> list[str]:
    """Load the bundled demo document into Safari Writer's buffer format."""

    text = files("safari_writer").joinpath(DEMO_DOCUMENT_RESOURCE).read_text(encoding=encoding)
    return decode_sfw(text)


def load_document_state(path: Path, encoding: str = "utf-8") -> AppState:
    """Load a document into an AppState instance."""

    state = AppState()
    state.buffer = load_document_buffer(path, encoding=encoding)
    state.filename = str(path)
    state.cursor_row = 0
    state.cursor_col = 0
    state.modified = False
    return state


def serialize_document_buffer(buffer: list[str], path: Path) -> str:
    """Serialize a buffer for writing to a target path."""

    if is_sfw(path.name):
        return encode_sfw(buffer)
    return "\n".join(strip_controls(buffer))
