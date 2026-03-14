"""Helpers for loading, detecting, and exporting slide decks."""

from __future__ import annotations

import re
from pathlib import Path, PurePosixPath
from typing import TYPE_CHECKING

from safari_slides.model import Presentation
from safari_slides.parser import parse_slidemd
from safari_slides.state import SafariSlidesState

if TYPE_CHECKING:
    from safari_writer.mail_merge_db import MailMergeDB
    from safari_writer.state import AppState, GlobalFormat

__all__ = [
    "build_slidemd_from_writer",
    "build_welcome_deck",
    "default_slide_export_name",
    "is_slide_filename",
    "load_presentation",
    "looks_like_slide_markdown",
    "slides_state_from_writer",
]

_SLIDE_SUFFIXES = {
    (".slides", ".md"),
    (".slide", ".md"),
}


def is_slide_filename(filename: str | Path | None) -> bool:
    """Return True when a file path strongly suggests SlideMD content."""

    if not filename:
        return False
    suffixes = tuple(s.lower() for s in PurePosixPath(str(filename)).suffixes)
    if suffixes and suffixes[-1] == ".slidemd":
        return True
    if len(suffixes) >= 2 and tuple(suffixes[-2:]) in _SLIDE_SUFFIXES:
        return True
    return False


def looks_like_slide_markdown(text: str) -> bool:
    """Heuristically detect whether text already looks like a slide deck."""

    normalized = text.replace("\r\n", "\n")
    signals = [
        bool(re.search(r"(?m)^---\s*$", normalized)),
        bool(re.search(r"(?m)^----\s*$", normalized)),
        "::: notes" in normalized.lower(),
        "<!-- fragment -->" in normalized,
        bool(re.search(r"(?m)^layout:\s+\w+", normalized)),
        bool(re.search(r"(?m)^aspect:\s+\d+:\d+", normalized)),
    ]
    return sum(1 for signal in signals if signal) >= 2


def load_presentation(path: Path) -> Presentation:
    """Load a SlideMD deck from disk."""

    source = path.read_text(encoding="utf-8")
    return parse_slidemd(source)


def build_welcome_deck() -> Presentation:
    """Return a small built-in deck for empty launches."""

    return parse_slidemd(
        """---
title: Safari Slides
theme: classic-blue
aspect: 4:3
footer: Safari Slides Preview
paginate: true
---

# Safari Slides

A keyboard-first presentation viewer with Atari-era flavor.

---

## Controls

- Right / Space: Next slide or fragment
- Left: Previous slide
- N: Toggle speaker notes
- Home / End: Jump to first or last slide
- Q / Esc: Return

Note:

Use Safari Writer's Print / Export menu to preview or export decks.
"""
    )


def default_slide_export_name(filename: str) -> str:
    """Return a sensible default output filename for SlideMD export."""

    if is_slide_filename(filename):
        return Path(filename).name
    if filename:
        source = Path(filename)
        stem = source.name
        if source.suffix:
            stem = source.stem
        return f"{stem}.slides.md"
    return "presentation.slides.md"


def build_slidemd_from_writer(
    buffer: list[str],
    fmt: GlobalFormat,
    db: MailMergeDB | None = None,
    *,
    title: str = "",
) -> str:
    """Convert a Safari Writer buffer into a SlideMD deck."""

    from safari_writer.export_md import export_markdown

    markdown = export_markdown(buffer, fmt, db).replace("\r\n", "\n").strip()
    if looks_like_slide_markdown(markdown):
        return markdown + "\n"

    sections = _sections_from_markdown(markdown)
    deck_title = title.strip() or _title_from_sections(sections) or "Safari Slides Deck"
    lines = [
        "---",
        f"title: {deck_title}",
        "theme: classic-blue",
        "aspect: 4:3",
        "paginate: true",
        "---",
        "",
    ]
    for index, section in enumerate(sections, start=1):
        if index > 1:
            lines.extend(["", "---", ""])
        lines.extend(_normalize_section(section, index))
    return "\n".join(lines).rstrip() + "\n"


def slides_state_from_writer(state: AppState) -> SafariSlidesState:
    """Build viewer state from the current Safari Writer document."""

    source_text = "\n".join(state.buffer)
    if is_slide_filename(state.filename) or looks_like_slide_markdown(source_text):
        deck_text = source_text
    else:
        deck_text = build_slidemd_from_writer(
            state.buffer,
            state.fmt,
            state.mail_merge_db,
            title=state.doc_title,
        )
    presentation = parse_slidemd(deck_text)
    slides_state = SafariSlidesState()
    slides_state.set_presentation(
        presentation,
        source_path=Path(state.filename).resolve() if state.filename else None,
        source_text=deck_text,
    )
    return slides_state


def _sections_from_markdown(markdown: str) -> list[list[str]]:
    raw_sections = [section.strip("\n") for section in re.split(r"(?m)^---\s*$", markdown)]
    sections = [section.splitlines() for section in raw_sections if section.strip()]
    if len(sections) > 1:
        return sections

    if sections:
        heading_split = _split_on_headings(sections[0])
        if len(heading_split) > 1:
            return heading_split
        paragraph_split = _split_on_paragraphs(sections[0])
        if paragraph_split:
            return paragraph_split
    return [["# Safari Slides", "", "No content available."]]


def _split_on_headings(lines: list[str]) -> list[list[str]]:
    groups: list[list[str]] = []
    current: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#") and current:
            groups.append(current)
            current = [line]
        else:
            current.append(line)
    if current:
        groups.append(current)
    return [group for group in groups if any(item.strip() for item in group)]


def _split_on_paragraphs(lines: list[str]) -> list[list[str]]:
    groups: list[list[str]] = []
    current: list[str] = []
    for line in lines:
        if not line.strip():
            if current:
                groups.append(current)
                current = []
            continue
        current.append(line)
    if current:
        groups.append(current)
    return groups


def _title_from_sections(sections: list[list[str]]) -> str:
    for section in sections:
        for line in section:
            stripped = line.strip()
            if stripped.startswith("#"):
                return stripped.lstrip("#").strip()
            if stripped:
                return stripped
    return ""


def _normalize_section(section: list[str], index: int) -> list[str]:
    if not section:
        return [f"# Slide {index}"]
    first_non_empty = next((line for line in section if line.strip()), "")
    if first_non_empty.startswith("#"):
        return section
    return [f"# Slide {index}", ""] + section

