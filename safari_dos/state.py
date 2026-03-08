"""State models for Safari DOS."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

__all__ = ["SafariDosExitRequest", "SafariDosState"]


@dataclass(frozen=True)
class SafariDosExitRequest:
    """Describe a handoff request emitted by the Safari DOS app."""

    action: str
    document_path: Path | None = None
    location_path: Path | None = None
    filename: str | None = None


@dataclass
class SafariDosState:
    """Mutable state shared across Safari DOS screens."""

    current_path: Path
    show_hidden: bool = False
    show_preview: bool = True
    fullscreen_preview: bool = False
    sort_field: str = "name"
    ascending: bool = True
    filter_text: str = ""
    selected_names: set[str] = field(default_factory=set)
    favorites: list[Path] = field(default_factory=list)
    recent_locations: list[Path] = field(default_factory=list)
    recent_documents: list[Path] = field(default_factory=list)
    pending_filename: str = ""
