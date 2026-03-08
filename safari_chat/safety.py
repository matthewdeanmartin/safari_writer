"""Crisis detection and safety responses for Safari Chat."""

from __future__ import annotations

import re

__all__ = [
    "crisis_response",
    "detect_crisis",
    "detect_refusal",
    "refusal_response",
]

# ---------------------------------------------------------------------------
# Crisis / self-harm detection patterns (case-insensitive)
# ---------------------------------------------------------------------------

_CRISIS_PATTERNS: list[re.Pattern[str]] = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"\b(kill|end)\s+(my\s*self|myself)\b",
        r"\bsuicid[ae]l?\b",
        r"\bwant\s+to\s+die\b",
        r"\bself[\s-]*harm\b",
        r"\bend\s+(it|everything)\s*(all|now|forever)?\b",
        r"\bgoodbye\b.*\b(forever|final|last)\b",
        r"\bdisappear\s+(forever|permanently)\b",
        r"\bdon'?t\s+want\s+to\s+(live|be\s+alive|exist)\b",
        r"\bno\s+reason\s+to\s+(live|go\s+on)\b",
        r"\bbetter\s+off\s+dead\b",
        r"\bwish\s+i\s+was\s+dead\b",
        r"\bhurt\s+my\s*self\b",
    ]
]

_REFUSAL_PATTERNS: list[re.Pattern[str]] = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"\bbest\s+way\s+to\s+kill\s+(my\s*self|myself)\b",
        r"\bhow\s+(to|do\s+i)\s+(kill|end|hurt)\s+(my\s*self|myself)\b",
        r"\bhow\s+to\s+(commit\s+)?suicide\b",
        r"\bhide\s+(self[\s-]*harm|cuts?|scars?)\b",
    ]
]

_CRISIS_TEMPLATE = (
    "I am very sorry that you are going through this. "
    "I am not a psychiatrist or crisis professional, and I should not "
    "pretend to be one. If you may act on these thoughts, please "
    "contact emergency services now, call a suicide or crisis hotline "
    "(such as 988 in the US), or reach out to a trusted person who can "
    "stay with you right away."
)

_REFUSAL_TEMPLATE = (
    "I am not able to help with that request. "
    "If you are in crisis, please contact emergency services or call "
    "a suicide/crisis hotline (such as 988 in the US). "
    "Please reach out to someone who can help."
)


def detect_crisis(text: str) -> bool:
    """Return True if *text* contains suicide or self-harm indicators."""
    return any(p.search(text) for p in _CRISIS_PATTERNS)


def detect_refusal(text: str) -> bool:
    """Return True if *text* requests actionable self-harm instructions."""
    return any(p.search(text) for p in _REFUSAL_PATTERNS)


def crisis_response() -> str:
    """Return the fixed crisis response template (never synonym-varied)."""
    return _CRISIS_TEMPLATE


def refusal_response() -> str:
    """Return the fixed refusal template for harmful requests."""
    return _REFUSAL_TEMPLATE
