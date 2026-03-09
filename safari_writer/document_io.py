"""Reusable document file helpers."""

from __future__ import annotations

from importlib.resources import files
from pathlib import Path

from safari_writer.file_types import resolve_file_profile, StorageMode
from safari_writer.format_codec import (
    decode_sfw,
    encode_sfw,
    extract_sfw_metadata,
    has_controls,
    inject_sfw_metadata,
    is_sfw,
    strip_controls,
)
from safari_writer.state import AppState

DEMO_DOCUMENT_RESOURCE = "demo_document.sfw"
DEMO_MAILMERGE_RESOURCE = "demo_mailmerge.json"

__all__ = [
    "DEMO_DOCUMENT_RESOURCE",
    "DEMO_MAILMERGE_RESOURCE",
    "load_demo_document_buffer",
    "load_demo_mail_merge_db",
    "load_document_buffer",
    "load_document_state",
    "load_sfw_language",
    "sanitize_plain_buffer",
    "serialize_document_buffer",
]


def load_document_buffer(
    path: Path, encoding: str = "utf-8",
) -> list[str]:
    """Load a document file into Safari Writer's in-memory buffer format."""

    text = path.read_text(encoding=encoding, errors="replace")
    if is_sfw(path.name):
        _meta, body = extract_sfw_metadata(text)
        return decode_sfw(body)
    return text.split("\n") if text else [""]


def load_sfw_language(path: Path, encoding: str = "utf-8") -> str:
    """Extract the ``%%lang:`` metadata from a ``.sfw`` file, or ``""``."""
    if not is_sfw(path.name):
        return ""
    text = path.read_text(encoding=encoding, errors="replace")
    meta, _ = extract_sfw_metadata(text)
    return meta.get("lang", "")


def load_demo_document_buffer(encoding: str = "utf-8") -> list[str]:
    """Load the bundled demo document into Safari Writer's buffer format."""

    text = (
        files("safari_writer")
        .joinpath(DEMO_DOCUMENT_RESOURCE)
        .read_text(encoding=encoding)
    )
    return decode_sfw(text)


def load_demo_mail_merge_db(encoding: str = "utf-8") -> "MailMergeDB":
    """Load the bundled demo mail merge database."""
    import json
    from safari_writer.mail_merge_db import MailMergeDB

    text = (
        files("safari_writer")
        .joinpath(DEMO_MAILMERGE_RESOURCE)
        .read_text(encoding=encoding)
    )
    data = json.loads(text)
    return MailMergeDB.from_dict(data)


def load_document_state(path: Path, encoding: str = "utf-8") -> AppState:
    """Load a document into an AppState instance."""

    state = AppState()
    state.buffer = load_document_buffer(path, encoding=encoding)
    state.filename = str(path)
    state.cursor_row = 0
    state.cursor_col = 0
    state.modified = False
    # Resolve file profile from filename
    state.file_profile = resolve_file_profile(path.name)
    # Per-document language (i18n Level 1)
    state.doc_language = load_sfw_language(path, encoding=encoding)
    # Sanitize buffer if loading a plain file that somehow has control chars
    if state.storage_mode == StorageMode.PLAIN and has_controls(state.buffer):
        state.buffer = strip_controls(state.buffer)
    return state


def sanitize_plain_buffer(buffer: list[str]) -> list[str]:
    """Strip Safari Writer control characters for plain-mode documents."""
    if has_controls(buffer):
        return strip_controls(buffer)
    return buffer


def serialize_document_buffer(
    buffer: list[str], path: Path, *, doc_language: str = "",
) -> str:
    """Serialize a buffer for writing to a target path.

    When *doc_language* is non-empty and the target is ``.sfw``, a
    ``%%lang:`` metadata header is prepended.
    """
    if is_sfw(path.name):
        body = encode_sfw(buffer)
        meta: dict[str, str] = {}
        if doc_language:
            meta["lang"] = doc_language
        return inject_sfw_metadata(meta, body)
    return "\n".join(strip_controls(buffer))
