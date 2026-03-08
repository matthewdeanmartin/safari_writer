"""Print / Export screens — modal menu and ANSI preview."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.screen import ModalScreen, Screen
from textual.widgets import Static
from textual import events

from safari_writer.heading_numbering import next_heading_number
from safari_writer.mail_merge_db import MailMergeDB
from safari_writer.state import AppState, GlobalFormat
from safari_writer.screens.editor import (
    CTRL_BOLD, CTRL_UNDERLINE, CTRL_CENTER, CTRL_RIGHT,
    CTRL_ELONGATE, CTRL_SUPER, CTRL_SUB, CTRL_PARA,
    CTRL_MERGE, CTRL_HEADER, CTRL_FOOTER, CTRL_HEADING,
    CTRL_EJECT, CTRL_CHAIN, CTRL_FORM, TOGGLE_MARKERS,
)


# -----------------------------------------------------------------------
# Print / Export menu
# -----------------------------------------------------------------------

PRINT_CSS = """
PrintScreen {
    align: center middle;
}

#print-dialog {
    width: 44;
    height: 11;
    border: solid $primary;
    background: $surface;
    padding: 1 2;
}

#print-title {
    text-align: center;
    text-style: bold;
    color: $accent;
    margin-bottom: 1;
}

.print-option {
    height: 1;
}

#print-hint {
    text-align: center;
    color: $text-muted;
    margin-top: 1;
}
"""


class PrintScreen(ModalScreen[str | None]):
    """Modal dialog offering print/export options.

    Dismisses with one of: "ansi", "markdown", "postscript", or None.
    """

    CSS = PRINT_CSS

    def compose(self) -> ComposeResult:
        from textual.containers import Container
        with Container(id="print-dialog"):
            yield Static("*** PRINT / EXPORT ***", id="print-title")
            yield Static("[bold underline]A[/]  ANSI Preview", classes="print-option")
            yield Static("[bold underline]M[/]  Export to Markdown (.md)", classes="print-option")
            yield Static("[bold underline]P[/]  Export to PostScript (.ps)", classes="print-option")
            yield Static("Esc  Cancel", id="print-hint")

    def on_key(self, event: events.Key) -> None:
        if event.key == "a":
            self.dismiss("ansi")
        elif event.key == "m":
            self.dismiss("markdown")
        elif event.key == "p":
            self.dismiss("postscript")
        elif event.key == "escape":
            self.dismiss(None)
        event.stop()


# -----------------------------------------------------------------------
# ANSI Print Preview
# -----------------------------------------------------------------------

PREVIEW_CSS = """
PrintPreviewScreen {
    background: $surface;
}

#preview-header {
    dock: top;
    height: 1;
    background: $primary;
    color: $text;
    padding: 0 1;
}

#preview-footer {
    dock: bottom;
    height: 1;
    background: $primary;
    color: $text;
    padding: 0 1;
}

#preview-body {
    height: 1fr;
    overflow-y: auto;
}
"""


class PrintPreviewScreen(Screen):
    """Full-screen read-only ANSI preview of the document."""

    CSS = PREVIEW_CSS

    def __init__(self, state: AppState) -> None:
        super().__init__()
        self.state = state
        self._rendered_lines: list[str] = []
        self._scroll_offset = 0
        self._total_pages = 1

    def compose(self) -> ComposeResult:
        yield Static("", id="preview-header")
        yield Static("", id="preview-body")
        yield Static(
            " PgUp/PgDn  Up/Down  Home/End  Esc=Close",
            id="preview-footer",
        )

    def on_mount(self) -> None:
        self._rendered_lines = _render_with_mail_merge(
            self.state.buffer, self.state.fmt, self.state.mail_merge_db
        )
        self._total_pages = _count_pages(self._rendered_lines)
        self._update_view()

    def _update_view(self) -> None:
        height = max(1, self.size.height - 2)  # minus header + footer
        visible = self._rendered_lines[self._scroll_offset : self._scroll_offset + height]
        body_text = "\n".join(visible)
        self.query_one("#preview-body", Static).update(body_text)

        page = _page_at_line(self._rendered_lines, self._scroll_offset)
        self.query_one("#preview-header", Static).update(
            f" PRINT PREVIEW — Page {page}/{self._total_pages}"
            f"   Line {self._scroll_offset + 1}/{len(self._rendered_lines)}"
        )

    def on_key(self, event: events.Key) -> None:
        height = max(1, self.size.height - 2)
        max_offset = max(0, len(self._rendered_lines) - height)

        if event.key == "escape":
            self.app.pop_screen()
        elif event.key == "up":
            self._scroll_offset = max(0, self._scroll_offset - 1)
            self._update_view()
        elif event.key == "down":
            self._scroll_offset = min(max_offset, self._scroll_offset + 1)
            self._update_view()
        elif event.key == "pageup":
            self._scroll_offset = max(0, self._scroll_offset - height)
            self._update_view()
        elif event.key == "pagedown":
            self._scroll_offset = min(max_offset, self._scroll_offset + height)
            self._update_view()
        elif event.key == "home":
            self._scroll_offset = 0
            self._update_view()
        elif event.key == "end":
            self._scroll_offset = max_offset
            self._update_view()

        event.stop()

    def on_resize(self) -> None:
        self._update_view()


# -----------------------------------------------------------------------
# Document rendering engine
# -----------------------------------------------------------------------

_PAGE_BREAK_MARKER = "__PAGE_BREAK__"


def _render_document(buffer: list[str], fmt: GlobalFormat) -> list[str]:
    """Render the document buffer into a list of Rich-markup lines for ANSI preview.

    Applies global format settings: margins, spacing, pagination, headers,
    footers, page numbering, justification.  Inline formatting is rendered
    with Rich markup tags.
    """
    left = fmt.left_margin
    right = fmt.right_margin
    width = max(right - left, 10)
    spacing_lines = max(1, fmt.line_spacing // 2)  # half-lines → screen lines
    para_extra = max(0, fmt.para_spacing // 2 - spacing_lines)
    indent = fmt.para_indent
    justify = fmt.justification == 1

    # First pass: extract headers, footers, and content lines
    header_text = ""
    footer_text = ""
    content_lines: list[str] = []
    heading_counters: list[int] = []

    for raw_line in buffer:
        if not raw_line:
            content_lines.append("")
            continue
        first = raw_line[0] if raw_line else ""
        if first == CTRL_HEADER:
            header_text = raw_line[1:]
            continue
        if first == CTRL_FOOTER:
            footer_text = raw_line[1:]
            continue
        if first == CTRL_CHAIN:
            # Chain file — show a note
            content_lines.append(f"[dim]>>> Chain: {raw_line[1:]}[/dim]")
            continue
        content_lines.append(raw_line)

    # Second pass: render content lines with formatting
    rendered: list[str] = []
    fmt_state = {m: False for m in TOGGLE_MARKERS}

    for raw_line in content_lines:
        # Page eject
        if raw_line and raw_line[0] == CTRL_EJECT:
            rendered.append(_PAGE_BREAK_MARKER)
            continue

        # Section heading
        if raw_line and raw_line[0] == CTRL_HEADING:
            level = raw_line[1] if len(raw_line) > 1 and raw_line[1].isdigit() else "1"
            number = next_heading_number(heading_counters, int(level))
            text = raw_line[2:] if len(raw_line) > 2 else ""
            clean = _strip_inline(text)
            heading = f"[bold]{number} {clean}[/bold]"
            rendered.append(_pad_left(heading, left))
            for _ in range(spacing_lines):
                rendered.append("")
            continue

        # Detect paragraph mark at start
        is_para = raw_line.startswith(CTRL_PARA)
        line_content = raw_line[1:] if is_para else raw_line

        # Detect alignment
        alignment = "left"
        if line_content.startswith(CTRL_CENTER):
            alignment = "center"
            line_content = line_content[1:]
        elif line_content.startswith(CTRL_RIGHT):
            alignment = "right"
            line_content = line_content[1:]

        # Render inline formatting
        styled, fmt_state = _render_inline(line_content, fmt_state)

        # Handle form blanks display
        # (already converted in _render_inline)

        # Apply indentation for paragraph marks
        if is_para:
            styled = " " * indent + styled

        # Apply alignment and width
        clean_len = _visible_length(styled)
        if alignment == "center":
            pad = max(0, (width - clean_len) // 2)
            styled = " " * pad + styled
        elif alignment == "right":
            pad = max(0, width - clean_len)
            styled = " " * pad + styled
        elif justify and clean_len < width:
            styled = _justify_line(styled, width)

        # Left margin
        styled = _pad_left(styled, left)

        # Empty line
        if raw_line == "":
            rendered.append("")
            for _ in range(para_extra):
                rendered.append("")
            continue

        rendered.append(styled)
        # Line spacing (extra blank lines between content lines)
        for _ in range(spacing_lines - 1):
            rendered.append("")

    # Paginate
    return _paginate(rendered, fmt, header_text, footer_text)


def _render_inline(
    text: str, fmt_state: dict[str, bool]
) -> tuple[str, dict[str, bool]]:
    """Convert a line with control chars into Rich-markup text."""
    out: list[str] = []
    i = 0
    while i < len(text):
        ch = text[i]
        if ch in TOGGLE_MARKERS:
            fmt_state[ch] = not fmt_state[ch]
            i += 1
            continue  # markers are invisible in print
        if ch == CTRL_MERGE:
            # Consume following digits for the field number
            i += 1
            digits: list[str] = []
            while i < len(text) and text[i].isdigit():
                digits.append(text[i])
                i += 1
            field_num = "".join(digits) if digits else "?"
            out.append(f"[cyan]<<@{field_num}>>[/cyan]")
            continue
        if ch == CTRL_FORM:
            out.append("[dim][________][/dim]")
            i += 1
            continue
        if ch == CTRL_PARA:
            i += 1
            continue  # consumed at line level
        # Any remaining non-printable control char — skip
        if ord(ch) < 0x20 and ch not in ("\t",):
            i += 1
            continue
        # Escape Rich markup
        if ch == "[":
            ch = "\\["
        # Apply current formatting
        markup = _inline_markup(fmt_state)
        if markup:
            out.append(f"[{markup}]{ch}[/{markup}]")
        else:
            out.append(ch)
        i += 1
    return "".join(out), fmt_state


def _inline_markup(fmt: dict[str, bool]) -> str:
    """Build a Rich markup tag from the current toggle state."""
    parts: list[str] = []
    if fmt.get(CTRL_BOLD):
        parts.append("bold")
    if fmt.get(CTRL_UNDERLINE):
        parts.append("underline")
    if fmt.get(CTRL_ELONGATE):
        parts.append("dim")
    if fmt.get(CTRL_SUPER) or fmt.get(CTRL_SUB):
        parts.append("bright_white")
    return " ".join(parts)


def _strip_inline(text: str) -> str:
    """Remove all control characters from text, returning plain content."""
    return "".join(ch for ch in text if ord(ch) >= 0x20 or ch == "\t")


def _visible_length(styled: str) -> int:
    """Estimate the visible length of a Rich-markup string.

    Strips ``[tag]`` sequences and backslash escapes to count only
    visible characters.  Not 100% precise but good enough for alignment.
    """
    import re
    clean = re.sub(r"\[/?[^\]]*\]", "", styled)
    clean = clean.replace("\\[", "[")
    return len(clean)


def _pad_left(text: str, spaces: int) -> str:
    return " " * spaces + text


def _justify_line(styled: str, width: int) -> str:
    """Very basic justification — just return as-is for now."""
    # Full justification would require splitting by words and adding spaces.
    # This is a placeholder; the line is already left-aligned.
    return styled


def _paginate(
    lines: list[str],
    fmt: GlobalFormat,
    header_text: str,
    footer_text: str,
) -> list[str]:
    """Split rendered lines into pages with headers, footers, and page numbers."""
    # Page body height in screen lines
    page_lines = max(fmt.page_length // 2, 10)  # half-lines → lines
    top_margin = max(fmt.top_margin // 2, 1)
    bottom_margin = max(fmt.bottom_margin // 2, 1)
    body_height = page_lines - top_margin - bottom_margin
    if body_height < 3:
        body_height = 3

    left = fmt.left_margin
    page_num = fmt.page_number_start
    output: list[str] = []

    # Separate content at page break markers
    pages_content: list[list[str]] = []
    current_page: list[str] = []
    for line in lines:
        if line == _PAGE_BREAK_MARKER:
            pages_content.append(current_page)
            current_page = []
        else:
            current_page.append(line)
    pages_content.append(current_page)

    # Now split each section into pages of body_height
    all_pages: list[list[str]] = []
    for section in pages_content:
        i = 0
        while i < len(section) or (i == 0 and not section):
            chunk = section[i : i + body_height]
            all_pages.append(chunk)
            i += body_height
            if i == 0:
                break  # empty section → one empty page

    if not all_pages:
        all_pages = [[""]]

    for page_idx, page_body in enumerate(all_pages):
        pn = page_num + page_idx

        # Top margin
        for _ in range(top_margin - 1):
            output.append("")

        # Header
        hdr = header_text.replace("@", str(pn)) if header_text else ""
        if hdr:
            output.append(_pad_left(f"[bold]{hdr}[/bold]", left))
        else:
            output.append("")

        # Body
        for line in page_body:
            output.append(line)

        # Pad remaining body space
        for _ in range(body_height - len(page_body)):
            output.append("")

        # Footer
        ftr = footer_text.replace("@", str(pn)) if footer_text else ""
        if ftr:
            output.append(_pad_left(f"[dim]{ftr}[/dim]", left))
        else:
            output.append("")

        # Bottom margin
        for _ in range(bottom_margin - 1):
            output.append("")

        # Page separator (visible rule between pages)
        if page_idx < len(all_pages) - 1:
            rule_width = max(fmt.right_margin, 40)
            output.append(f"[dim]{'─' * rule_width}  Page {pn}[/dim]")

    return output


def _buffer_has_merge_markers(buffer: list[str]) -> bool:
    """Return True if any line contains a mail merge marker."""
    return any(CTRL_MERGE in line for line in buffer)


def _render_with_mail_merge(
    buffer: list[str],
    fmt: GlobalFormat,
    db: MailMergeDB | None,
) -> list[str]:
    """Render with mail merge substitution when applicable.

    If the buffer contains merge markers and a DB with records is loaded,
    renders one copy per record with page breaks between copies.
    Otherwise renders the buffer as-is.
    """
    if not _buffer_has_merge_markers(buffer) or db is None or not db.records:
        return _render_document(buffer, fmt)

    all_lines: list[str] = []
    for rec_idx, record in enumerate(db.records):
        merged_buf = _apply_record(buffer, record)
        rendered = _render_document(merged_buf, fmt)
        if rec_idx > 0:
            rule_width = max(fmt.right_margin, 40)
            all_lines.append(f"[bold cyan]{'═' * rule_width}  Record {rec_idx + 1}[/bold cyan]")
        all_lines.extend(rendered)
    return all_lines


def _apply_record(buffer: list[str], record: list[str]) -> list[str]:
    """Substitute merge markers in buffer with values from one record."""
    merged: list[str] = []
    for line in buffer:
        out: list[str] = []
        i = 0
        while i < len(line):
            ch = line[i]
            if ch == CTRL_MERGE:
                i += 1
                digits: list[str] = []
                while i < len(line) and line[i].isdigit():
                    digits.append(line[i])
                    i += 1
                if digits:
                    field_num = int("".join(digits))
                    if 1 <= field_num <= len(record):
                        out.append(record[field_num - 1])
                    else:
                        out.append(f"<<@{field_num}>>")
                else:
                    out.append("<<@?>>")
                continue
            out.append(ch)
            i += 1
        merged.append("".join(out))
    return merged


def _count_pages(rendered: list[str]) -> int:
    """Count pages by looking for page separator rules."""
    count = 1
    for line in rendered:
        if "─" in line and "Page " in line:
            count += 1
    return count


def _page_at_line(rendered: list[str], offset: int) -> int:
    """Determine which page a given scroll offset falls on."""
    page = 1
    for i in range(offset):
        if i < len(rendered) and "─" in rendered[i] and "Page " in rendered[i]:
            page += 1
    return page
