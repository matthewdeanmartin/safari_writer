"""Reusable proofing helpers for TUI and CLI flows."""

from __future__ import annotations

import re
from pathlib import Path

_CTRL_CHARS = re.compile(r"[\x01-\x1f]")

__all__ = [
    "check_word",
    "dict_lookup",
    "extract_words",
    "load_personal_dictionary",
    "make_checker",
    "suggest_words",
]


def make_checker():
    """Return an enchant dictionary, or None if unavailable."""

    try:
        import enchant

        return enchant.Dict("en_US")
    except Exception:
        return None


def check_word(word: str, checker, kept: set[str], personal: set[str]) -> bool:
    """Return True if word is correctly spelled."""

    stripped = word.strip(".,;:!?\"'()-")
    if not stripped or not stripped[0].isalpha():
        return True
    lowered = stripped.lower()
    if lowered in kept or lowered in personal:
        return True
    if checker is None:
        return True
    return checker.check(stripped)


def suggest_words(word: str, checker) -> list[str]:
    """Return candidate spellings for a word."""

    if checker is None:
        return []
    try:
        return checker.suggest(word)[:18]
    except Exception:
        return []


def dict_lookup(prefix: str, checker) -> list[str]:
    """Return dictionary words starting with a prefix."""

    if checker is None or len(prefix) < 2:
        return []
    try:
        suggestions = checker.suggest(prefix)
    except Exception:
        return []
    matches = [word for word in suggestions if word.lower().startswith(prefix.lower())]
    return matches[:126]


def extract_words(buffer: list[str]) -> list[tuple[int, int, str]]:
    """Yield (row, col, word) for every word token in the buffer."""

    word_re = re.compile(r"[A-Za-z']+")
    results: list[tuple[int, int, str]] = []
    for row, line in enumerate(buffer):
        clean = _CTRL_CHARS.sub(" ", line)
        for match in word_re.finditer(clean):
            results.append((row, match.start(), match.group()))
    return results


def load_personal_dictionary(path: Path, encoding: str = "utf-8") -> set[str]:
    """Load personal-dictionary words from disk."""

    text = path.read_text(encoding=encoding)
    words = re.split(r"[\s\n]+", text.strip().lower())
    return {word for word in words if word}
