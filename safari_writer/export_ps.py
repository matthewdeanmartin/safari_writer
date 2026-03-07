"""Export document buffer to PostScript format.

Generates a .ps file with full page layout using GlobalFormat settings.
The output can be printed directly or converted to PDF with ps2pdf.
"""

from __future__ import annotations

from safari_writer.heading_numbering import next_heading_number
from safari_writer.state import GlobalFormat
from safari_writer.screens.editor import (
    CTRL_BOLD, CTRL_UNDERLINE, CTRL_CENTER, CTRL_RIGHT,
    CTRL_ELONGATE, CTRL_SUPER, CTRL_SUB, CTRL_PARA,
    CTRL_MERGE, CTRL_HEADER, CTRL_FOOTER, CTRL_HEADING,
    CTRL_EJECT, CTRL_CHAIN, CTRL_FORM,
)

# PostScript points per inch
_PPI = 72
# US Letter dimensions in points
_PAGE_W = int(8.5 * _PPI)  # 612
_PAGE_H = int(11.0 * _PPI)  # 792

# Font mapping from type_font setting
_FONTS: dict[int, tuple[str, str, float]] = {
    # type_font: (regular_font, bold_font, size_pt)
    1: ("Courier", "Courier-Bold", 10),            # pica
    2: ("Courier", "Courier-Bold", 7),              # condensed
    3: ("Helvetica", "Helvetica-Bold", 10),          # proportional
    6: ("Courier", "Courier-Bold", 8.5),             # elite
}

# Character width approximation (monospace at given size)
def _char_width(font_size: float) -> float:
    return font_size * 0.6


def export_postscript(buffer: list[str], fmt: GlobalFormat) -> str:
    """Convert a document buffer to PostScript source text."""
    reg_font, bold_font, font_size = _FONTS.get(fmt.type_font, _FONTS[1])
    char_w = _char_width(font_size)
    line_height = font_size * (fmt.line_spacing / 2.0) * 1.2

    # Margins in points
    left_margin_pt = fmt.left_margin * char_w
    right_margin_pt = fmt.right_margin * char_w
    top_margin_pt = fmt.top_margin * (font_size * 0.6)
    bottom_margin_pt = fmt.bottom_margin * (font_size * 0.6)
    text_width = right_margin_pt - left_margin_pt
    if text_width < 72:
        text_width = 72

    usable_height = _PAGE_H - top_margin_pt - bottom_margin_pt
    lines_per_page = max(3, int(usable_height / line_height))

    indent_pt = fmt.para_indent * char_w

    # First pass: extract headers, footers, content
    header_text = ""
    footer_text = ""
    content: list[_Line] = []
    heading_counters: list[int] = []

    for raw_line in buffer:
        if not raw_line:
            content.append(_Line("", align="left", is_blank=True))
            continue
        first = raw_line[0]
        if first == CTRL_HEADER:
            header_text = _strip(raw_line[1:])
            continue
        if first == CTRL_FOOTER:
            footer_text = _strip(raw_line[1:])
            continue
        if first == CTRL_CHAIN:
            continue  # ignored in PS output
        if first == CTRL_EJECT:
            content.append(_Line("", page_break=True))
            continue
        if first == CTRL_HEADING:
            level_ch = raw_line[1] if len(raw_line) > 1 and raw_line[1].isdigit() else "1"
            level = int(level_ch)
            text = raw_line[2:] if len(raw_line) > 2 else ""
            clean = _strip(text)
            number = next_heading_number(heading_counters, level)
            content.append(_Line(f"{number} {clean}", bold=True))
            continue

        is_para = raw_line.startswith(CTRL_PARA)
        line_text = raw_line[1:] if is_para else raw_line

        align = "left"
        if line_text.startswith(CTRL_CENTER):
            align = "center"
            line_text = line_text[1:]
        elif line_text.startswith(CTRL_RIGHT):
            align = "right"
            line_text = line_text[1:]

        spans = _parse_spans(line_text)
        content.append(_Line(
            "", align=align, indent=is_para, spans=spans,
        ))

    # Paginate
    pages: list[list[_Line]] = []
    current: list[_Line] = []
    for ln in content:
        if ln.page_break:
            pages.append(current)
            current = []
            continue
        current.append(ln)
        if len(current) >= lines_per_page:
            pages.append(current)
            current = []
    if current or not pages:
        pages.append(current)

    # Generate PostScript
    ps = _PSWriter()
    ps.header(reg_font, bold_font, font_size)

    for page_idx, page_lines in enumerate(pages):
        pn = fmt.page_number_start + page_idx
        ps.begin_page(pn)

        y = _PAGE_H - top_margin_pt

        # Header
        if header_text:
            hdr = header_text.replace("@", str(pn))
            ps.set_font(bold_font, font_size)
            ps.show_text(left_margin_pt, y, hdr)
            ps.set_font(reg_font, font_size)
        y -= line_height * 2  # gap after header

        # Body lines
        for ln in page_lines:
            if ln.is_blank:
                y -= line_height
                continue

            x = left_margin_pt
            if ln.indent:
                x += indent_pt

            if ln.bold:
                # Simple bold line (headings)
                ps.set_font(bold_font, font_size)
                ps.show_text(x, y, _ps_escape(ln.text))
                ps.set_font(reg_font, font_size)
            elif ln.spans:
                # Render spans with formatting
                line_str = "".join(s.text for s in ln.spans)
                total_w = len(line_str) * char_w

                if ln.align == "center":
                    x = left_margin_pt + max(0, (text_width - total_w) / 2)
                elif ln.align == "right":
                    x = left_margin_pt + max(0, text_width - total_w)

                for span in ln.spans:
                    if not span.text:
                        continue
                    if span.bold or span.elongated:
                        ps.set_font(bold_font, font_size)
                    else:
                        ps.set_font(reg_font, font_size)

                    if span.underline:
                        ps.underline_on()

                    if span.superscript:
                        ps.show_text(x, y + font_size * 0.3, _ps_escape(span.text))
                    elif span.subscript:
                        ps.show_text(x, y - font_size * 0.3, _ps_escape(span.text))
                    else:
                        ps.show_text(x, y, _ps_escape(span.text))

                    if span.underline:
                        span_w = len(span.text) * char_w
                        ps.underline_draw(x, y, span_w)

                    x += len(span.text) * char_w
                    ps.set_font(reg_font, font_size)
            else:
                ps.show_text(x, y, "")

            y -= line_height

        # Footer
        if footer_text:
            ftr_y = bottom_margin_pt
            ftr = footer_text.replace("@", str(pn))
            ps.set_font(reg_font, font_size * 0.9)
            ps.show_text(left_margin_pt, ftr_y, ftr)
            ps.set_font(reg_font, font_size)

        ps.end_page()

    ps.trailer()
    return ps.output()


# -----------------------------------------------------------------------
# Internal data types
# -----------------------------------------------------------------------

class _Span:
    __slots__ = ("text", "bold", "underline", "elongated", "superscript", "subscript")

    def __init__(
        self, text: str = "", *,
        bold: bool = False, underline: bool = False,
        elongated: bool = False, superscript: bool = False,
        subscript: bool = False,
    ):
        self.text = text
        self.bold = bold
        self.underline = underline
        self.elongated = elongated
        self.superscript = superscript
        self.subscript = subscript


class _Line:
    __slots__ = ("text", "align", "indent", "bold", "is_blank", "page_break", "spans")

    def __init__(
        self, text: str = "", *,
        align: str = "left", indent: bool = False,
        bold: bool = False, is_blank: bool = False,
        page_break: bool = False, spans: list[_Span] | None = None,
    ):
        self.text = text
        self.align = align
        self.indent = indent
        self.bold = bold
        self.is_blank = is_blank
        self.page_break = page_break
        self.spans = spans


def _parse_spans(text: str) -> list[_Span]:
    """Parse inline controls into styled spans."""
    spans: list[_Span] = []
    current_chars: list[str] = []
    bold = underline = elongated = superscript = subscript = False

    def flush():
        if current_chars:
            spans.append(_Span(
                "".join(current_chars),
                bold=bold, underline=underline, elongated=elongated,
                superscript=superscript, subscript=subscript,
            ))
            current_chars.clear()

    for ch in text:
        if ch == CTRL_BOLD:
            flush()
            bold = not bold
        elif ch == CTRL_UNDERLINE:
            flush()
            underline = not underline
        elif ch == CTRL_ELONGATE:
            flush()
            elongated = not elongated
        elif ch == CTRL_SUPER:
            flush()
            superscript = not superscript
        elif ch == CTRL_SUB:
            flush()
            subscript = not subscript
        elif ch == CTRL_MERGE:
            flush()
            spans.append(_Span("<<@>>"))
        elif ch == CTRL_FORM:
            flush()
            spans.append(_Span("[________]"))
        elif ch == CTRL_PARA:
            continue
        elif ord(ch) < 0x20 and ch != "\t":
            continue
        else:
            current_chars.append(ch)

    flush()
    return spans


def _strip(text: str) -> str:
    """Remove all control characters."""
    return "".join(ch for ch in text if ord(ch) >= 0x20 or ch == "\t")


def _ps_escape(text: str) -> str:
    """Escape special PostScript characters in a string literal."""
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


# -----------------------------------------------------------------------
# PostScript writer
# -----------------------------------------------------------------------

class _PSWriter:
    """Minimal PostScript DSC document builder."""

    def __init__(self):
        self._buf: list[str] = []
        self._page_count = 0

    def header(self, reg_font: str, bold_font: str, size: float):
        self._buf.append("%!PS-Adobe-3.0")
        self._buf.append(f"%%BoundingBox: 0 0 {_PAGE_W} {_PAGE_H}")
        self._buf.append("%%Pages: (atend)")
        self._buf.append(f"%%DocumentFonts: {reg_font} {bold_font}")
        self._buf.append("%%EndComments")
        self._buf.append("")
        # Define convenience procedures
        self._buf.append("/SF { findfont exch scalefont setfont } bind def")
        self._buf.append("/S { moveto show } bind def")
        self._buf.append("")

    def begin_page(self, page_num: int):
        self._page_count += 1
        self._buf.append(f"%%Page: {page_num} {self._page_count}")

    def end_page(self):
        self._buf.append("showpage")
        self._buf.append("")

    def set_font(self, name: str, size: float):
        self._buf.append(f"{size} /{name} SF")

    def show_text(self, x: float, y: float, text: str):
        self._buf.append(f"({text}) {x:.1f} {y:.1f} S")

    def underline_on(self):
        pass  # state tracked externally

    def underline_draw(self, x: float, y: float, width: float):
        self._buf.append(f"newpath {x:.1f} {y - 1:.1f} moveto "
                         f"{width:.1f} 0 rlineto 0.5 setlinewidth stroke")

    def trailer(self):
        self._buf.append(f"%%Pages: {self._page_count}")
        self._buf.append("%%EOF")

    def output(self) -> str:
        return "\n".join(self._buf) + "\n"
