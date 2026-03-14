"""File type awareness — classify files by extension for storage mode and highlighting.

See spec/10_file_type_awareness.md for the full design.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from enum import Enum
from pathlib import PurePosixPath

__all__ = [
    "FileProfile",
    "HighlightProfile",
    "StorageMode",
    "resolve_file_profile",
]


class StorageMode(Enum):
    """Whether the buffer may contain Safari Writer control codes."""

    FORMATTED = "formatted"
    PLAIN = "plain"


class HighlightProfile(Enum):
    """Syntax/prose highlighting strategy for the editor."""

    SAFARI_WRITER = "safari-writer"
    PLAIN_TEXT = "plain-text"
    MARKDOWN = "markdown"
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    JSON = "json"
    TOML = "toml"
    YAML = "yaml"
    INI = "ini"
    SAFARI_BASIC = "safari-basic"
    SAFARI_ASM = "safari-asm"
    SAFARI_BASE = "safari-base"
    ENGLISH_TEXT = "english-text"
    ENGLISH_MARKDOWN = "english-markdown"


# Final suffix → base highlight profile
_SUFFIX_MAP: dict[str, HighlightProfile] = {
    ".sfw": HighlightProfile.SAFARI_WRITER,
    ".txt": HighlightProfile.PLAIN_TEXT,
    ".md": HighlightProfile.MARKDOWN,
    ".py": HighlightProfile.PYTHON,
    ".js": HighlightProfile.JAVASCRIPT,
    ".ts": HighlightProfile.TYPESCRIPT,
    ".json": HighlightProfile.JSON,
    ".toml": HighlightProfile.TOML,
    ".yaml": HighlightProfile.YAML,
    ".yml": HighlightProfile.YAML,
    ".ini": HighlightProfile.INI,
    ".cfg": HighlightProfile.INI,
    ".bas": HighlightProfile.SAFARI_BASIC,
    ".asm": HighlightProfile.SAFARI_ASM,
    ".prg": HighlightProfile.SAFARI_BASE,
}

# English overlay: (lang_suffix, base_profile) → overlay profile
_ENGLISH_OVERLAYS: dict[tuple[str, HighlightProfile], HighlightProfile] = {
    (".en", HighlightProfile.PLAIN_TEXT): HighlightProfile.ENGLISH_TEXT,
    (".en", HighlightProfile.MARKDOWN): HighlightProfile.ENGLISH_MARKDOWN,
}

# Profile → Pygments lexer name (for code/data types)
PYGMENTS_LEXER_MAP: dict[HighlightProfile, str] = {
    HighlightProfile.PYTHON: "python",
    HighlightProfile.JAVASCRIPT: "javascript",
    HighlightProfile.TYPESCRIPT: "typescript",
    HighlightProfile.JSON: "json",
    HighlightProfile.TOML: "toml",
    HighlightProfile.YAML: "yaml",
    HighlightProfile.INI: "ini",
    HighlightProfile.MARKDOWN: "markdown",
    HighlightProfile.SAFARI_BASIC: "basic",
    HighlightProfile.SAFARI_ASM: "asm",
    HighlightProfile.SAFARI_BASE: "foxpro",
}

# Human-readable display names
_DISPLAY_NAMES: dict[HighlightProfile, str] = {
    HighlightProfile.SAFARI_WRITER: "Safari Writer",
    HighlightProfile.PLAIN_TEXT: "Plain Text",
    HighlightProfile.MARKDOWN: "Markdown",
    HighlightProfile.PYTHON: "Python",
    HighlightProfile.JAVASCRIPT: "JavaScript",
    HighlightProfile.TYPESCRIPT: "TypeScript",
    HighlightProfile.JSON: "JSON",
    HighlightProfile.TOML: "TOML",
    HighlightProfile.YAML: "YAML",
    HighlightProfile.INI: "INI",
    HighlightProfile.SAFARI_BASIC: "Safari Basic",
    HighlightProfile.SAFARI_ASM: "Safari ASM",
    HighlightProfile.SAFARI_BASE: "Safari Base",
    HighlightProfile.ENGLISH_TEXT: "English Text",
    HighlightProfile.ENGLISH_MARKDOWN: "English Markdown",
}


@dataclass(frozen=True)
class FileProfile:
    """Resolved file type information for a document."""

    storage_mode: StorageMode
    highlight_profile: HighlightProfile
    display_name: str

    @property
    def allows_formatting_codes(self) -> bool:
        return self.storage_mode == StorageMode.FORMATTED

    @property
    def is_code(self) -> bool:
        return self.highlight_profile in PYGMENTS_LEXER_MAP

    @property
    def is_english(self) -> bool:
        return self.highlight_profile in (
            HighlightProfile.ENGLISH_TEXT,
            HighlightProfile.ENGLISH_MARKDOWN,
        )

    @property
    def pygments_lexer(self) -> str | None:
        return PYGMENTS_LEXER_MAP.get(self.highlight_profile)


def _parse_suffixes(filename: str) -> list[str]:
    """Extract lowered suffixes from a filename, handling multi-part extensions."""
    # Use PurePosixPath for consistent behavior
    name = os.path.basename(filename)
    # Get all suffixes: "chapter.en.md" → [".en", ".md"]
    p = PurePosixPath(name)
    return [s.lower() for s in p.suffixes]


def resolve_file_profile(filename: str) -> FileProfile:
    """Determine storage mode and highlight profile from a filename.

    Rules (see spec §5):
    1. Final suffix .sfw → formatted storage + safari-writer highlight.
    2. Otherwise → plain storage + suffix-based highlight.
    3. Penultimate .en suffix upgrades to english-text or english-markdown.
    """
    suffixes = _parse_suffixes(filename)

    # Storage mode: only .sfw is formatted
    final_suffix = suffixes[-1] if suffixes else ""
    if final_suffix == ".sfw":
        storage_mode = StorageMode.FORMATTED
    else:
        storage_mode = StorageMode.PLAIN

    # Base highlight profile from final suffix
    base_profile = _SUFFIX_MAP.get(final_suffix, HighlightProfile.PLAIN_TEXT)

    # Check for natural-language overlay (penultimate suffix)
    highlight_profile = base_profile
    if len(suffixes) >= 2:
        lang_suffix = suffixes[-2]
        overlay_key = (lang_suffix, base_profile)
        if overlay_key in _ENGLISH_OVERLAYS:
            highlight_profile = _ENGLISH_OVERLAYS[overlay_key]

    display_name = _DISPLAY_NAMES.get(highlight_profile, "Plain Text")

    return FileProfile(
        storage_mode=storage_mode,
        highlight_profile=highlight_profile,
        display_name=display_name,
    )
