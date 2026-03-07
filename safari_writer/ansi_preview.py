"""Public helpers for headless ANSI preview rendering."""

from __future__ import annotations

from safari_writer.screens.print_screen import _count_pages, _render_document
from safari_writer.state import GlobalFormat

__all__ = ["count_ansi_pages", "extract_ansi_page", "render_ansi_preview"]


def render_ansi_preview(buffer: list[str], fmt: GlobalFormat) -> list[str]:
    """Render a document buffer into ANSI-preview lines."""

    return _render_document(buffer, fmt)


def count_ansi_pages(rendered: list[str]) -> int:
    """Count rendered ANSI-preview pages."""

    return _count_pages(rendered)


def extract_ansi_page(rendered: list[str], page_number: int) -> list[str]:
    """Return a single 1-based page from rendered ANSI-preview lines."""

    pages: list[list[str]] = [[]]
    for line in rendered:
        if "─" in line and "Page " in line:
            pages.append([])
            continue
        pages[-1].append(line)
    if page_number < 1 or page_number > len(pages):
        raise ValueError(f"Page {page_number} is out of range for {len(pages)} page(s)")
    return pages[page_number - 1]
