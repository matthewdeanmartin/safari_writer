"""Public interface for Safari Slides."""

from safari_slides.app import SafariSlidesApp
from safari_slides.main import build_parser, main, parse_args
from safari_slides.model import (Presentation, PresentationMetadata,
                                 RenderLine, Slide, SlideMetadata)
from safari_slides.parser import parse_slidemd
from safari_slides.services import (build_slidemd_from_writer,
                                    build_welcome_deck,
                                    default_slide_export_name,
                                    is_slide_filename, load_presentation,
                                    looks_like_slide_markdown,
                                    slides_state_from_writer)
from safari_slides.state import SafariSlidesState

__all__ = [
    "Presentation",
    "PresentationMetadata",
    "RenderLine",
    "SafariSlidesApp",
    "SafariSlidesState",
    "Slide",
    "SlideMetadata",
    "build_parser",
    "build_slidemd_from_writer",
    "build_welcome_deck",
    "default_slide_export_name",
    "is_slide_filename",
    "load_presentation",
    "looks_like_slide_markdown",
    "main",
    "parse_args",
    "parse_slidemd",
    "slides_state_from_writer",
]
