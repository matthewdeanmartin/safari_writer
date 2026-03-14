"""Mutable viewer state for Safari Slides."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from safari_slides.model import Presentation, Slide

__all__ = ["SafariSlidesState"]


@dataclass
class SafariSlidesState:
    """Shared state for the slide viewer screen."""

    presentation: Presentation = field(default_factory=Presentation)
    current_slide_index: int = 0
    fragment_step: int = 0
    show_notes: bool = False
    source_path: Path | None = None
    source_text: str = ""

    @property
    def slide_count(self) -> int:
        return len(self.presentation.slides)

    @property
    def current_slide(self) -> Slide:
        if not self.presentation.slides:
            raise RuntimeError("Safari Slides presentation is empty.")
        return self.presentation.slides[self.current_slide_index]

    def reset_view(self) -> None:
        self.current_slide_index = 0
        self.fragment_step = 0
        self.show_notes = False

    def set_presentation(
        self,
        presentation: Presentation,
        *,
        source_path: Path | None = None,
        source_text: str = "",
    ) -> None:
        self.presentation = presentation
        self.source_path = source_path
        self.source_text = source_text
        self.reset_view()

    def advance(self) -> None:
        slide = self.current_slide
        if self.fragment_step < slide.fragment_count:
            self.fragment_step += 1
            return
        if self.current_slide_index < self.slide_count - 1:
            self.current_slide_index += 1
            self.fragment_step = 0

    def retreat(self) -> None:
        if self.fragment_step > 0:
            self.fragment_step -= 1
            return
        if self.current_slide_index > 0:
            self.current_slide_index -= 1
            self.fragment_step = self.current_slide.fragment_count

    def first_slide(self) -> None:
        self.current_slide_index = 0
        self.fragment_step = 0

    def last_slide(self) -> None:
        if not self.presentation.slides:
            return
        self.current_slide_index = self.slide_count - 1
        self.fragment_step = self.current_slide.fragment_count

