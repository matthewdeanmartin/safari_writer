"""Semantic SlideMD presentation models."""

from __future__ import annotations

from dataclasses import dataclass, field

__all__ = [
    "Presentation",
    "PresentationMetadata",
    "RenderLine",
    "Slide",
    "SlideMetadata",
]


@dataclass(frozen=True)
class PresentationMetadata:
    """Document-level metadata for a slide deck."""

    title: str = ""
    author: str = ""
    date: str = ""
    theme: str = "classic-blue"
    aspect: str = "4:3"
    footer: str = ""
    paginate: bool = True
    extra: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class SlideMetadata:
    """Per-slide metadata extracted from SlideMD."""

    layout: str = "default"
    background: str = ""
    css_class: str = ""
    transition: str = ""
    footer: str = ""
    autoplay: int | None = None
    extra: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class RenderLine:
    """A visible line in the terminal renderer."""

    text: str
    fragment_order: int = 0


@dataclass(frozen=True)
class Slide:
    """A single slide in presentation order."""

    slide_id: str
    title: str
    raw_markdown: str
    metadata: SlideMetadata = field(default_factory=SlideMetadata)
    notes: tuple[str, ...] = ()
    lines: tuple[RenderLine, ...] = ()
    horizontal_index: int = 1
    vertical_index: int = 1

    @property
    def fragment_count(self) -> int:
        """Return the number of incremental reveal steps on this slide."""

        return max((line.fragment_order for line in self.lines), default=0)

    @property
    def slide_label(self) -> str:
        """Return a human-readable slide coordinate."""

        if self.vertical_index > 1:
            return f"{self.horizontal_index}.{self.vertical_index}"
        return str(self.horizontal_index)


@dataclass(frozen=True)
class Presentation:
    """A parsed SlideMD deck."""

    metadata: PresentationMetadata = field(default_factory=PresentationMetadata)
    slides: tuple[Slide, ...] = ()

