"""Synonym variation system for Safari Chat."""

from __future__ import annotations

import random
import re

__all__ = ["apply_variation"]

# ---------------------------------------------------------------------------
# Synonym sets (spec section 7.4 + extras)
# ---------------------------------------------------------------------------

SYNONYM_SETS: dict[str, list[str]] = {
    "frustrating": ["frustrating", "aggravating", "exasperating", "upsetting"],
    "calm": ["calm", "steady", "grounded", "settled"],
    "understand": ["understand", "see", "appreciate", "recognize"],
    "difficult": ["difficult", "hard", "tough", "challenging"],
    "work through": ["work through", "go through", "step through", "walk through"],
    "confusing": ["confusing", "unclear", "muddled", "bewildering"],
    "problem": ["problem", "issue", "snag", "hiccup"],
}

# Phrase-level synonyms where we match and replace the whole phrase
# (avoids doubling like "very very sorry" or "can I guidance you").
_PHRASE_SETS: dict[str, list[str]] = {
    "I am sorry": [
        "I am sorry",
        "I am very sorry",
        "I am truly sorry",
        "I am terribly sorry",
    ],
    "I am terribly sorry": [
        "I am terribly sorry",
        "I am very sorry",
        "I am truly sorry",
    ],
    "I am very sorry": [
        "I am very sorry",
        "I am terribly sorry",
        "I am truly sorry",
    ],
    "I am truly sorry": [
        "I am truly sorry",
        "I am very sorry",
        "I am terribly sorry",
    ],
}

# Pre-compiled patterns for word-level synonyms (word-boundary, case-insensitive).
_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(rf"\b{re.escape(key)}\b", re.IGNORECASE), key)
    for key in sorted(SYNONYM_SETS, key=len, reverse=True)  # longest first
]

# Pre-compiled patterns for phrase-level synonyms (longest first).
_PHRASE_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(re.escape(key), re.IGNORECASE), key)
    for key in sorted(_PHRASE_SETS, key=len, reverse=True)
]


def _match_case(original: str, replacement: str) -> str:
    """Roughly preserve the case style of *original* in *replacement*."""
    if original.isupper():
        return replacement.upper()
    if original and original[0].isupper():
        return replacement[0].upper() + replacement[1:]
    return replacement


def apply_variation(
    text: str,
    *,
    max_substitutions: int = 3,
    seed: int | None = None,
    protect_safety: bool = False,
) -> str:
    """Apply controlled synonym substitution to *text*.

    If *protect_safety* is ``True`` the text is returned unchanged (used for
    crisis responses that must stay verbatim).
    """
    if protect_safety:
        return text

    rng = random.Random(seed)
    subs_done = 0

    # Try phrase-level substitutions first (e.g. "I am sorry" -> "I am truly sorry").
    for pattern, key in _PHRASE_PATTERNS:
        if subs_done >= max_substitutions:
            break
        match = pattern.search(text)
        if match:
            alternatives = [
                s for s in _PHRASE_SETS[key] if s.lower() != match.group(0).lower()
            ]
            if not alternatives:
                continue
            replacement = rng.choice(alternatives)
            replacement = _match_case(match.group(0), replacement)
            text = text[: match.start()] + replacement + text[match.end() :]
            subs_done += 1

    # Then word-level substitutions.
    for pattern, key in _PATTERNS:
        if subs_done >= max_substitutions:
            break
        match = pattern.search(text)
        if match:
            alternatives = [s for s in SYNONYM_SETS[key] if s != match.group(0).lower()]
            if not alternatives:
                continue
            replacement = rng.choice(alternatives)
            replacement = _match_case(match.group(0), replacement)
            text = text[: match.start()] + replacement + text[match.end() :]
            subs_done += 1

    return text
