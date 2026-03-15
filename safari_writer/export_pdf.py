"""Export document buffers to PDF."""

from __future__ import annotations

from dataclasses import dataclass, field
from io import BytesIO
from typing import TYPE_CHECKING

from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen.canvas import Canvas

from safari_writer.heading_numbering import next_heading_number
from safari_writer.state import GlobalFormat

if TYPE_CHECKING:
    from safari_writer.export_ps import _Span
    from safari_writer.mail_merge_db import MailMergeDB

from safari_writer.export_ps import _FONTS, _PAGE_H, _PAGE_W, _parse_spans, _strip
from safari_writer.screens.editor import (
    CTRL_CENTER,
    CTRL_CHAIN,
    CTRL_EJECT,
    CTRL_FOOTER,
    CTRL_HEADER,
    CTRL_HEADING,
    CTRL_MERGE,
    CTRL_PARA,
    CTRL_RIGHT,
)

__all__ = ["export_pdf"]


@dataclass(slots=True)
class _PdfLine:
    text: str = ""
    align: str = "left"
    indent: bool = False
    bold: bool = False
    is_blank: bool = False
    page_break: bool = False
    spans: list[_Span] = field(default_factory=list)


def export_pdf(
    buffer: list[str],
    fmt: GlobalFormat,
    db: MailMergeDB | None = None,
    is_markdown: bool = False,
) -> bytes:
    """Convert a document buffer to PDF bytes."""
    stream = BytesIO()
    pdf = Canvas(stream, pagesize=(_PAGE_W, _PAGE_H), pageCompression=0)

    if is_markdown:
        from safari_writer.export_ps import _markdown_to_sfw_like_buffer

        buffer = _markdown_to_sfw_like_buffer(buffer)

    has_merge = any(CTRL_MERGE in line for line in buffer)
    if has_merge and db is not None and db.records:
        from safari_writer.mail_merge_db import apply_mail_merge_to_buffer

        for rec_idx in range(len(db.records)):
            original_records = db.records
            db.records = [db.records[rec_idx]]
            merged_buffer = apply_mail_merge_to_buffer(buffer, db)
            db.records = original_records
            _render_single(pdf, merged_buffer, fmt)
    else:
        _render_single(pdf, buffer, fmt)

    pdf.save()
    return stream.getvalue()


def _render_single(pdf: Canvas, buffer: list[str], fmt: GlobalFormat) -> None:
    reg_font, bold_font, font_size = _FONTS.get(fmt.type_font, _FONTS[1])
    char_width = _char_width(font_size)
    line_height = font_size * (fmt.line_spacing / 2.0) * 1.2

    left_margin_pt = fmt.left_margin * char_width
    right_margin_pt = fmt.right_margin * char_width
    top_margin_pt = fmt.top_margin * (font_size * 0.6)
    bottom_margin_pt = fmt.bottom_margin * (font_size * 0.6)
    text_width = max(72.0, right_margin_pt - left_margin_pt)
    usable_height = _PAGE_H - top_margin_pt - bottom_margin_pt
    lines_per_page = max(3, int(usable_height / line_height))
    indent_pt = fmt.para_indent * char_width

    header_text, footer_text, pages = _paginate(buffer, lines_per_page)

    for page_idx, page_lines in enumerate(pages):
        page_number = fmt.page_number_start + page_idx
        y = _PAGE_H - top_margin_pt

        if header_text:
            pdf.setFont(bold_font, font_size)
            pdf.drawString(
                left_margin_pt, y, header_text.replace("@", str(page_number))
            )
            pdf.setFont(reg_font, font_size)
        y -= line_height * 2

        for line in page_lines:
            if line.is_blank:
                y -= line_height
                continue

            x = left_margin_pt + (indent_pt if line.indent else 0.0)
            if line.bold:
                pdf.setFont(bold_font, font_size)
                pdf.drawString(x, y, line.text)
                pdf.setFont(reg_font, font_size)
                y -= line_height
                continue

            if line.spans:
                x = _aligned_x(
                    line,
                    left_margin_pt,
                    text_width,
                    reg_font,
                    bold_font,
                    font_size,
                    x,
                )
                for span in line.spans:
                    if not span.text:
                        continue
                    span_font = bold_font if span.bold or span.elongated else reg_font
                    span_width = stringWidth(span.text, span_font, font_size)
                    pdf.setFont(span_font, font_size)

                    text_y = y
                    if span.superscript:
                        text_y += font_size * 0.3
                    elif span.subscript:
                        text_y -= font_size * 0.3

                    pdf.drawString(x, text_y, span.text)

                    if span.underline:
                        pdf.line(x, y - 1, x + span_width, y - 1)

                    x += span_width

            y -= line_height

        if footer_text:
            pdf.setFont(reg_font, font_size * 0.9)
            pdf.drawString(
                left_margin_pt,
                bottom_margin_pt,
                footer_text.replace("@", str(page_number)),
            )
            pdf.setFont(reg_font, font_size)

        pdf.showPage()


def _paginate(
    buffer: list[str], lines_per_page: int
) -> tuple[str, str, list[list[_PdfLine]]]:
    header_text = ""
    footer_text = ""
    content: list[_PdfLine] = []
    heading_counters: list[int] = []

    for raw_line in buffer:
        if not raw_line:
            content.append(_PdfLine(is_blank=True))
            continue

        first = raw_line[0]
        if first == CTRL_HEADER:
            header_text = _strip(raw_line[1:])
            continue
        if first == CTRL_FOOTER:
            footer_text = _strip(raw_line[1:])
            continue
        if first == CTRL_CHAIN:
            continue
        if first == CTRL_EJECT:
            content.append(_PdfLine(page_break=True))
            continue
        if first == CTRL_HEADING:
            level_ch = (
                raw_line[1] if len(raw_line) > 1 and raw_line[1].isdigit() else "1"
            )
            level = int(level_ch)
            text = raw_line[2:] if len(raw_line) > 2 else ""
            number = next_heading_number(heading_counters, level)
            content.append(_PdfLine(text=f"{number} {_strip(text)}", bold=True))
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

        content.append(
            _PdfLine(
                align=align,
                indent=is_para,
                spans=_parse_spans(line_text),
            )
        )

    pages: list[list[_PdfLine]] = []
    current: list[_PdfLine] = []
    for line in content:
        if line.page_break:
            pages.append(current)
            current = []
            continue
        current.append(line)
        if len(current) >= lines_per_page:
            pages.append(current)
            current = []
    if current or not pages:
        pages.append(current)

    return header_text, footer_text, pages


def _aligned_x(
    line: _PdfLine,
    left_margin_pt: float,
    text_width: float,
    reg_font: str,
    bold_font: str,
    font_size: float,
    default_x: float,
) -> float:
    if line.align == "left":
        return default_x

    total_width = 0.0
    for span in line.spans:
        span_font = bold_font if span.bold or span.elongated else reg_font
        total_width += stringWidth(span.text, span_font, font_size)

    if line.align == "center":
        return left_margin_pt + max(0.0, (text_width - total_width) / 2.0)
    if line.align == "right":
        return left_margin_pt + max(0.0, text_width - total_width)
    return default_x


def _char_width(font_size: float) -> float:
    return font_size * 0.6
