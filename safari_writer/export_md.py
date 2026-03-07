"""Export document buffer to Markdown format."""

from __future__ import annotations

from typing import TYPE_CHECKING

from safari_writer.heading_numbering import next_heading_number
from safari_writer.state import GlobalFormat

if TYPE_CHECKING:
    from safari_writer.mail_merge_db import MailMergeDB

from safari_writer.screens.editor import (
    CTRL_BOLD, CTRL_UNDERLINE, CTRL_CENTER, CTRL_RIGHT,
    CTRL_ELONGATE, CTRL_SUPER, CTRL_SUB, CTRL_PARA,
    CTRL_MERGE, CTRL_HEADER, CTRL_FOOTER, CTRL_HEADING,
    CTRL_EJECT, CTRL_CHAIN, CTRL_FORM, TOGGLE_MARKERS,
)

__all__ = ["export_markdown"]


def export_markdown(
    buffer: list[str],
    fmt: GlobalFormat,
    db: MailMergeDB | None = None,
) -> str:
    """Convert a document buffer to Markdown text.

    If the buffer contains merge markers and *db* has records, one copy of
    the document is emitted per record with field values substituted.

    Mapping:
      Bold        → **...**
      Underline   → <u>...</u>
      Elongated   → **...** (treated as bold)
      Superscript → <sup>...</sup>
      Subscript   → <sub>...</sub>
      Center      → <center>...</center>
      Flush right → <!-- flush right --> prefix
      Header line → text at top (not # heading)
      Footer line → text at bottom
      Heading N   → # repeated N times
      Page break  → ---
      Para mark   → blank line
      Chain file  → <!-- chain: filename -->
      Form blank  → [________]
      Merge field → {{fieldN}}
    """
    has_merge = any(CTRL_MERGE in line for line in buffer)
    if has_merge and db is not None and db.records:
        from safari_writer.mail_merge_db import apply_mail_merge_to_buffer
        parts: list[str] = []
        for rec_idx in range(len(db.records)):
            # Temporarily set the first record for apply_mail_merge_to_buffer
            single_db_records = db.records
            original_records = db.records
            db.records = [db.records[rec_idx]]
            merged_buf = apply_mail_merge_to_buffer(buffer, db)
            db.records = original_records
            if rec_idx > 0:
                parts.append("\n---\n")
            parts.append(_export_single(merged_buf, fmt))
        return "\n".join(parts)
    return _export_single(buffer, fmt)


def _export_single(buffer: list[str], fmt: GlobalFormat) -> str:
    """Export a single copy of the document (no mail merge iteration)."""
    header_lines: list[str] = []
    footer_lines: list[str] = []
    body_lines: list[str] = []
    heading_counters: list[int] = []

    for raw_line in buffer:
        if not raw_line:
            body_lines.append("")
            continue

        first = raw_line[0]

        # Header / footer — collect separately
        if first == CTRL_HEADER:
            header_lines.append(_convert_inline(raw_line[1:]))
            continue
        if first == CTRL_FOOTER:
            footer_lines.append(_convert_inline(raw_line[1:]))
            continue

        # Chain file
        if first == CTRL_CHAIN:
            body_lines.append(f"<!-- chain: {raw_line[1:]} -->")
            continue

        # Page eject
        if first == CTRL_EJECT:
            body_lines.append("")
            body_lines.append("---")
            body_lines.append("")
            continue

        # Section heading
        if first == CTRL_HEADING:
            level_ch = raw_line[1] if len(raw_line) > 1 and raw_line[1].isdigit() else "1"
            level = int(level_ch)
            text = raw_line[2:] if len(raw_line) > 2 else ""
            clean = _strip_controls(text)
            number = next_heading_number(heading_counters, level)
            body_lines.append(f"{'#' * level} {number} {clean}")
            body_lines.append("")
            continue

        # Paragraph mark → blank line before the indented content
        if first == CTRL_PARA:
            body_lines.append("")
            body_lines.append(_convert_line(raw_line[1:]))
            continue

        body_lines.append(_convert_line(raw_line))

    # Assemble output
    parts: list[str] = []
    if header_lines:
        parts.extend(header_lines)
        parts.append("")
    parts.extend(body_lines)
    if footer_lines:
        parts.append("")
        parts.extend(footer_lines)

    return "\n".join(parts) + "\n"


def _convert_line(raw_line: str) -> str:
    """Convert a single content line, handling alignment prefixes."""
    if not raw_line:
        return ""

    # Alignment
    if raw_line.startswith(CTRL_CENTER):
        inner = _convert_inline(raw_line[1:])
        return f"<center>{inner}</center>"
    if raw_line.startswith(CTRL_RIGHT):
        inner = _convert_inline(raw_line[1:])
        return f"<!-- flush right -->{inner}"

    return _convert_inline(raw_line)


def _convert_inline(text: str) -> str:
    """Process inline formatting controls into Markdown syntax."""
    # We need to track toggle state and wrap spans.
    # Strategy: walk the text, when a toggle opens emit the opening tag,
    # when it closes emit the closing tag.

    out: list[str] = []
    state: dict[str, bool] = {
        CTRL_BOLD: False,
        CTRL_UNDERLINE: False,
        CTRL_ELONGATE: False,
        CTRL_SUPER: False,
        CTRL_SUB: False,
    }

    # Tag pairs: (control, open, close)
    _TAGS = {
        CTRL_BOLD:      ("**", "**"),
        CTRL_UNDERLINE: ("<u>", "</u>"),
        CTRL_ELONGATE:  ("**", "**"),
        CTRL_SUPER:     ("<sup>", "</sup>"),
        CTRL_SUB:       ("<sub>", "</sub>"),
    }

    i = 0
    while i < len(text):
        ch = text[i]
        if ch in TOGGLE_MARKERS:
            was_on = state[ch]
            state[ch] = not was_on
            open_tag, close_tag = _TAGS[ch]
            out.append(close_tag if was_on else open_tag)
            i += 1
            continue
        if ch == CTRL_MERGE:
            i += 1
            digits: list[str] = []
            while i < len(text) and text[i].isdigit():
                digits.append(text[i])
                i += 1
            field_num = "".join(digits) if digits else "?"
            out.append("{{" + f"field{field_num}" + "}}")
            continue
        if ch == CTRL_FORM:
            out.append("[________]")
            i += 1
            continue
        if ch == CTRL_PARA:
            i += 1
            continue  # handled at line level
        # Skip other control chars
        if ord(ch) < 0x20 and ch not in ("\t",):
            i += 1
            continue
        out.append(ch)
        i += 1

    # Close any unclosed toggles at end of line
    for ctrl in (CTRL_BOLD, CTRL_ELONGATE, CTRL_UNDERLINE, CTRL_SUPER, CTRL_SUB):
        if state[ctrl]:
            _, close_tag = _TAGS[ctrl]
            out.append(close_tag)
            state[ctrl] = False

    return "".join(out)


def _strip_controls(text: str) -> str:
    """Remove all control characters, returning plain text."""
    return "".join(ch for ch in text if ord(ch) >= 0x20 or ch == "\t")
