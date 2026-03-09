"""State models for Safari REPL."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

__all__ = ["ReplExitRequest", "ReplState"]


@dataclass(frozen=True)
class ReplExitRequest:
    """Describe a handoff request emitted by the Safari REPL app."""

    action: str  # "quit" | "open-in-writer"
    document_path: Path | None = None


@dataclass
class ReplState:
    """Mutable state shared across Safari REPL screens."""

    loaded_path: Path | None = None
    history: list[str] = field(default_factory=list)
    output_lines: list[str] = field(default_factory=list)
