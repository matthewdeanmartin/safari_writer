"""Parser for the SlideMD presentation format."""

from __future__ import annotations

import re
from dataclasses import replace

from safari_slides.model import (Presentation, PresentationMetadata,
                                 RenderLine, Slide, SlideMetadata)

__all__ = ["parse_slidemd"]

_IMAGE_RE = re.compile(r"!\[(?P<alt>[^\]]*)\]\((?P<path>[^)]+)\)(?:\{[^}]*\})?")
_CENTER_RE = re.compile(r"<center>(.*?)</center>")
_COMMENT_RE = re.compile(r"<!--.*?-->")


def parse_slidemd(text: str) -> Presentation:
    """Parse SlideMD text into a presentation model."""

    normalized = text.replace("\r\n", "\n").replace("\r", "\n").strip("\n")
    if not normalized:
        return Presentation(
            metadata=PresentationMetadata(title="Untitled Presentation"),
            slides=(
                Slide(
                    slide_id="slide-1",
                    title="Untitled Presentation",
                    raw_markdown="# Untitled Presentation",
                    lines=(RenderLine("# Untitled Presentation"),),
                ),
            ),
        )

    document_meta, remainder = _extract_leading_metadata_block(normalized)
    metadata = _presentation_metadata(document_meta)

    sections = _split_slide_sections(remainder)
    slides: list[Slide] = []
    for index, (section_text, horizontal_index, vertical_index) in enumerate(
        sections, start=1
    ):
        slide_meta_map, slide_body = _extract_leading_metadata_block(section_text)
        slide_meta = _slide_metadata(slide_meta_map)
        body_lines, notes = _split_notes(slide_body)
        render_lines = tuple(_render_lines(body_lines))
        title = _extract_title(body_lines, metadata.title, index)
        slides.append(
            Slide(
                slide_id=f"slide-{index}",
                title=title,
                raw_markdown=section_text.strip("\n"),
                metadata=slide_meta,
                notes=notes,
                lines=render_lines,
                horizontal_index=horizontal_index,
                vertical_index=vertical_index,
            )
        )

    if not slides:
        slides.append(
            Slide(
                slide_id="slide-1",
                title=metadata.title or "Untitled Presentation",
                raw_markdown="",
                lines=(RenderLine("# Untitled Presentation"),),
            )
        )
    if not metadata.title:
        metadata = replace(metadata, title=slides[0].title)
    return Presentation(metadata=metadata, slides=tuple(slides))


def _extract_leading_metadata_block(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}, text
    block = text[4:end]
    metadata = _parse_metadata(block)
    if not metadata:
        return {}, text
    remainder = text[end + 5 :].lstrip("\n")
    return metadata, remainder


def _parse_metadata(block: str) -> dict[str, str]:
    data: dict[str, str] = {}
    for raw_line in block.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if ":" not in line:
            return {}
        key, value = line.split(":", 1)
        data[key.strip().lower()] = value.strip().strip('"').strip("'")
    return data


def _presentation_metadata(data: dict[str, str]) -> PresentationMetadata:
    extra = {
        key: value
        for key, value in data.items()
        if key
        not in {"title", "author", "date", "theme", "aspect", "footer", "paginate"}
    }
    return PresentationMetadata(
        title=data.get("title", ""),
        author=data.get("author", ""),
        date=data.get("date", ""),
        theme=data.get("theme", "classic-blue") or "classic-blue",
        aspect=data.get("aspect", "4:3") or "4:3",
        footer=data.get("footer", ""),
        paginate=_parse_bool(data.get("paginate", "true")),
        extra=extra,
    )


def _slide_metadata(data: dict[str, str]) -> SlideMetadata:
    extra = {
        key: value
        for key, value in data.items()
        if key
        not in {"layout", "background", "class", "transition", "footer", "autoplay"}
    }
    autoplay_raw = data.get("autoplay", "").strip()
    autoplay = int(autoplay_raw) if autoplay_raw.isdigit() else None
    return SlideMetadata(
        layout=data.get("layout", "default") or "default",
        background=data.get("background", ""),
        css_class=data.get("class", ""),
        transition=data.get("transition", ""),
        footer=data.get("footer", ""),
        autoplay=autoplay,
        extra=extra,
    )


def _split_slide_sections(text: str) -> list[tuple[str, int, int]]:
    if not text.strip():
        return []
    sections: list[tuple[str, int, int]] = []
    buffer: list[str] = []
    horizontal_index = 1
    vertical_index = 1
    in_code_fence = False
    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if stripped.startswith("```"):
            in_code_fence = not in_code_fence
        if not in_code_fence and stripped in {"---", "----"}:
            section_text = "\n".join(buffer).strip("\n")
            if section_text:
                sections.append((section_text, horizontal_index, vertical_index))
            buffer = []
            if stripped == "---":
                horizontal_index += 1
                vertical_index = 1
            else:
                vertical_index += 1
            continue
        buffer.append(raw_line)
    tail = "\n".join(buffer).strip("\n")
    if tail:
        sections.append((tail, horizontal_index, vertical_index))
    merged_sections: list[tuple[str, int, int]] = []
    pending_metadata: tuple[str, int, int] | None = None
    for section_text, section_horizontal, section_vertical in sections:
        if _is_metadata_section(section_text):
            pending_metadata = (section_text, section_horizontal, section_vertical)
            continue
        if pending_metadata is not None:
            metadata_text, meta_horizontal, meta_vertical = pending_metadata
            section_text = f"---\n{metadata_text}\n---\n\n{section_text}"
            merged_sections.append((section_text, meta_horizontal, meta_vertical))
            pending_metadata = None
            continue
        merged_sections.append((section_text, section_horizontal, section_vertical))
    if pending_metadata is not None:
        metadata_text, meta_horizontal, meta_vertical = pending_metadata
        merged_sections.append(
            (f"---\n{metadata_text}\n---", meta_horizontal, meta_vertical)
        )
    return merged_sections


def _split_notes(slide_text: str) -> tuple[list[str], tuple[str, ...]]:
    body_lines: list[str] = []
    notes: list[str] = []
    in_notes_block = False
    directive_notes = False
    for raw_line in slide_text.splitlines():
        stripped = raw_line.strip()
        if directive_notes:
            if stripped == ":::":
                directive_notes = False
                continue
            notes.append(raw_line.rstrip())
            continue
        if in_notes_block:
            notes.append(raw_line.rstrip())
            continue
        if stripped.lower() == "note:":
            in_notes_block = True
            continue
        if stripped.lower() == "::: notes":
            directive_notes = True
            continue
        body_lines.append(raw_line.rstrip())
    cleaned_notes = tuple(line for line in (note.strip() for note in notes) if line)
    return body_lines, cleaned_notes


def _render_lines(lines: list[str]) -> list[RenderLine]:
    render_lines: list[RenderLine] = []
    fragment_order = 0
    for raw_line in lines:
        stripped = raw_line.strip()
        if stripped.lower().startswith(":::"):
            if render_lines and render_lines[-1].text:
                render_lines.append(RenderLine(""))
            continue
        text = _normalize_visible_text(raw_line)
        if stripped.startswith("+ "):
            fragment_order += 1
            render_lines.append(RenderLine("- " + stripped[2:], fragment_order))
            continue
        if "<!-- fragment -->" in raw_line:
            fragment_order += 1
            text = text.replace("<!-- fragment -->", "").rstrip()
            render_lines.append(RenderLine(text, fragment_order))
            continue
        if text or not render_lines or render_lines[-1].text:
            render_lines.append(RenderLine(text))
    while render_lines and not render_lines[-1].text:
        render_lines.pop()
    return render_lines


def _normalize_visible_text(line: str) -> str:
    centered = _CENTER_RE.sub(r"\1", line)
    images = _IMAGE_RE.sub(lambda match: f"[Image: {match.group('path')}]", centered)
    comments_removed = _COMMENT_RE.sub("", images)
    return comments_removed.rstrip()


def _extract_title(lines: list[str], presentation_title: str, index: int) -> str:
    for raw_line in lines:
        stripped = raw_line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            return stripped.lstrip("#").strip()
        return stripped
    if presentation_title:
        return presentation_title
    return f"Slide {index}"


def _parse_bool(value: str) -> bool:
    return value.strip().lower() not in {"false", "0", "off", "no"}


def _is_metadata_section(section_text: str) -> bool:
    lines = [line.strip() for line in section_text.splitlines() if line.strip()]
    if not lines:
        return False
    if any(line.startswith(("#", "-", "*", "+", ">")) for line in lines):
        return False
    return bool(_parse_metadata("\n".join(lines)))
