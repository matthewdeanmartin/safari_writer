"""Syntax and prose highlighting for the editor using Rich/Pygments.

Provides Textual-compatible styled text (rich.text.Text) for each line,
layered on top of base content. The editor composites these with Safari Writer
formatting, selection, and cursor layers.

See spec/10_file_type_awareness.md §9–10.
"""

from __future__ import annotations

import re

from rich.style import Style
from rich.text import Text

from safari_writer.file_types import (PYGMENTS_LEXER_MAP, FileProfile,
                                      HighlightProfile)

__all__ = [
    "highlight_line",
    "highlight_buffer",
    "create_highlighter",
]


# ---------------------------------------------------------------------------
# Pygments-based code highlighting
# ---------------------------------------------------------------------------


def _pygments_highlight_buffer(lines: list[str], lexer_name: str) -> list[Text]:
    """Highlight an entire buffer using Pygments and return one Text per line."""
    from pygments.lexers import get_lexer_by_name
    from rich.syntax import Syntax

    try:
        get_lexer_by_name(lexer_name)
    except Exception:
        return [Text(line) for line in lines]

    result: list[Text] = []
    for line in lines:
        if not line.strip():
            result.append(Text(line))
            continue
        syn = Syntax(line, lexer_name, theme="monokai", line_numbers=False)
        highlighted = syn.highlight(line)
        result.append(highlighted)

    return result


# ---------------------------------------------------------------------------
# English prose highlighting (minimal — full system comes later)
# ---------------------------------------------------------------------------

# Function words: prepositions, conjunctions, articles, pronouns, auxiliary verbs
_FUNCTION_WORDS = frozenset(
    {
        # Articles
        "a",
        "an",
        "the",
        # Prepositions
        "at",
        "by",
        "for",
        "from",
        "in",
        "into",
        "of",
        "on",
        "to",
        "with",
        "about",
        "above",
        "across",
        "after",
        "against",
        "along",
        "among",
        "around",
        "before",
        "behind",
        "below",
        "beneath",
        "beside",
        "between",
        "beyond",
        "during",
        "except",
        "inside",
        "near",
        "off",
        "onto",
        "outside",
        "over",
        "past",
        "through",
        "toward",
        "towards",
        "under",
        "until",
        "upon",
        "within",
        "without",
        # Conjunctions
        "and",
        "but",
        "or",
        "nor",
        "so",
        "yet",
        "for",
        "although",
        "because",
        "since",
        "unless",
        "while",
        "whereas",
        "if",
        "then",
        "that",
        "than",
        "whether",
        # Pronouns
        "i",
        "me",
        "my",
        "mine",
        "myself",
        "you",
        "your",
        "yours",
        "yourself",
        "he",
        "him",
        "his",
        "himself",
        "she",
        "her",
        "hers",
        "herself",
        "it",
        "its",
        "itself",
        "we",
        "us",
        "our",
        "ours",
        "ourselves",
        "they",
        "them",
        "their",
        "theirs",
        "themselves",
        "who",
        "whom",
        "whose",
        "which",
        "what",
        "this",
        "that",
        "these",
        "those",
        # Auxiliary / modal verbs
        "is",
        "am",
        "are",
        "was",
        "were",
        "be",
        "been",
        "being",
        "have",
        "has",
        "had",
        "having",
        "do",
        "does",
        "did",
        "will",
        "would",
        "shall",
        "should",
        "can",
        "could",
        "may",
        "might",
        "must",
        # Other function words
        "not",
        "no",
        "very",
        "too",
        "also",
        "just",
        "only",
        "as",
        "how",
        "when",
        "where",
        "why",
    }
)

# Editorial markers
_EDITORIAL_RE = re.compile(r"\b(TODO|FIXME|NOTE|WARNING|HACK|XXX)\b")

# URL pattern
_URL_RE = re.compile(r"https?://\S+|www\.\S+")

# Email pattern
_EMAIL_RE = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")

# Numbers and dates
_NUMBER_RE = re.compile(r"\b\d[\d,.:/-]*\b")

# Markdown heading
_MD_HEADING_RE = re.compile(r"^(#{1,6})\s")

# Markdown emphasis
_MD_BOLD_RE = re.compile(r"(\*\*|__)(.*?)\1")
_MD_ITALIC_RE = re.compile(r"(?<!\*)(\*|_)(?!\*)(.*?)\1")

# Markdown code
_MD_CODE_RE = re.compile(r"`([^`]+)`")

# Markdown list markers
_MD_LIST_RE = re.compile(r"^(\s*)([-*+]|\d+\.)\s")

# Markdown blockquote
_MD_QUOTE_RE = re.compile(r"^(>\s*)+")

# Markdown link
_MD_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")

# Punctuation
_PUNCT_RE = re.compile(r'[.,;:!?()"\'\[\]{}<>—–…]+')

# Styles for prose highlighting
_STYLE_FUNCTION_WORD = Style(color="bright_black")
_STYLE_PUNCTUATION = Style(color="bright_black")
_STYLE_EDITORIAL = Style(color="bright_yellow", bold=True)
_STYLE_URL = Style(color="bright_cyan", underline=True)
_STYLE_EMAIL = Style(color="bright_cyan")
_STYLE_NUMBER = Style(color="bright_magenta")
_STYLE_MD_HEADING = Style(color="bright_green", bold=True)
_STYLE_MD_BOLD = Style(bold=True)
_STYLE_MD_ITALIC = Style(italic=True)
_STYLE_MD_CODE = Style(color="bright_yellow")
_STYLE_MD_LIST = Style(color="bright_green")
_STYLE_MD_QUOTE = Style(color="bright_blue")
_STYLE_MD_LINK_TEXT = Style(color="bright_cyan")
_STYLE_MD_LINK_URL = Style(color="bright_blue", underline=True)


def _highlight_english_line(line: str, include_markdown: bool = False) -> Text:
    """Apply English prose highlighting to a single line."""
    text = Text(line)

    if not line.strip():
        return text

    # Markdown structure (if enabled)
    if include_markdown:
        # Headings
        m = _MD_HEADING_RE.match(line)
        if m:
            text.stylize(_STYLE_MD_HEADING, 0, len(line))
            return text

        # Blockquotes
        m = _MD_QUOTE_RE.match(line)
        if m:
            text.stylize(_STYLE_MD_QUOTE, 0, m.end())

        # List markers
        m = _MD_LIST_RE.match(line)
        if m:
            text.stylize(_STYLE_MD_LIST, m.start(2), m.end(2))

        # Bold
        for m in _MD_BOLD_RE.finditer(line):
            text.stylize(_STYLE_MD_BOLD, m.start(), m.end())

        # Italic
        for m in _MD_ITALIC_RE.finditer(line):
            text.stylize(_STYLE_MD_ITALIC, m.start(), m.end())

        # Inline code
        for m in _MD_CODE_RE.finditer(line):
            text.stylize(_STYLE_MD_CODE, m.start(), m.end())

        # Links
        for m in _MD_LINK_RE.finditer(line):
            text.stylize(_STYLE_MD_LINK_TEXT, m.start(1), m.end(1))
            text.stylize(_STYLE_MD_LINK_URL, m.start(2), m.end(2))

    # Editorial markers (TODO, FIXME, etc.)
    for m in _EDITORIAL_RE.finditer(line):
        text.stylize(_STYLE_EDITORIAL, m.start(), m.end())

    # URLs
    for m in _URL_RE.finditer(line):
        text.stylize(_STYLE_URL, m.start(), m.end())

    # Emails
    for m in _EMAIL_RE.finditer(line):
        text.stylize(_STYLE_EMAIL, m.start(), m.end())

    # Numbers
    for m in _NUMBER_RE.finditer(line):
        text.stylize(_STYLE_NUMBER, m.start(), m.end())

    # Function words and punctuation — tokenize by word boundaries
    for m in re.finditer(r"\b(\w+)\b", line):
        word = m.group(1)
        if word.lower() in _FUNCTION_WORDS:
            text.stylize(_STYLE_FUNCTION_WORD, m.start(), m.end())

    # Punctuation
    for m in _PUNCT_RE.finditer(line):
        text.stylize(_STYLE_PUNCTUATION, m.start(), m.end())

    return text


# ---------------------------------------------------------------------------
# Markdown highlighting (non-English, code-only)
# ---------------------------------------------------------------------------


def _highlight_markdown_line(line: str) -> Text:
    """Apply Markdown structure highlighting without English prose overlay."""
    text = Text(line)

    if not line.strip():
        return text

    # Headings
    m = _MD_HEADING_RE.match(line)
    if m:
        text.stylize(_STYLE_MD_HEADING, 0, len(line))
        return text

    # Blockquotes
    m = _MD_QUOTE_RE.match(line)
    if m:
        text.stylize(_STYLE_MD_QUOTE, 0, m.end())

    # List markers
    m = _MD_LIST_RE.match(line)
    if m:
        text.stylize(_STYLE_MD_LIST, m.start(2), m.end(2))

    # Bold
    for m in _MD_BOLD_RE.finditer(line):
        text.stylize(_STYLE_MD_BOLD, m.start(), m.end())

    # Italic
    for m in _MD_ITALIC_RE.finditer(line):
        text.stylize(_STYLE_MD_ITALIC, m.start(), m.end())

    # Inline code
    for m in _MD_CODE_RE.finditer(line):
        text.stylize(_STYLE_MD_CODE, m.start(), m.end())

    # Links
    for m in _MD_LINK_RE.finditer(line):
        text.stylize(_STYLE_MD_LINK_TEXT, m.start(1), m.end(1))
        text.stylize(_STYLE_MD_LINK_URL, m.start(2), m.end(2))

    return text


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


class Highlighter:
    """Stateful highlighter for a document buffer based on its file profile."""

    def __init__(self, profile: FileProfile) -> None:
        self.profile = profile
        self._cache: list[Text] | None = None
        self._cache_key: tuple[int, ...] | None = None

    def highlight_buffer(self, lines: list[str]) -> list[Text]:
        """Return highlighted Text objects for each line of the buffer.

        Uses caching: only re-highlights when the buffer content changes.
        """
        # Simple cache key: tuple of line hashes
        key = tuple(hash(line) for line in lines)
        if self._cache is not None and self._cache_key == key:
            return self._cache

        hp = self.profile.highlight_profile

        if hp == HighlightProfile.SAFARI_WRITER:
            # SFW uses its own rendering; return unstyled text
            result = [Text(line) for line in lines]
        elif hp in PYGMENTS_LEXER_MAP:
            lexer_name = PYGMENTS_LEXER_MAP[hp]
            result = _pygments_highlight_buffer(lines, lexer_name)
        elif hp == HighlightProfile.ENGLISH_TEXT:
            result = [
                _highlight_english_line(line, include_markdown=False) for line in lines
            ]
        elif hp == HighlightProfile.ENGLISH_MARKDOWN:
            result = [
                _highlight_english_line(line, include_markdown=True) for line in lines
            ]
        elif hp == HighlightProfile.PLAIN_TEXT:
            result = [Text(line) for line in lines]
        else:
            result = [Text(line) for line in lines]

        self._cache = result
        self._cache_key = key
        return result

    def highlight_line(self, line: str, line_index: int = 0) -> Text:
        """Highlight a single line (uncached, for incremental updates)."""
        hp = self.profile.highlight_profile

        if hp == HighlightProfile.SAFARI_WRITER:
            return Text(line)
        elif hp in PYGMENTS_LEXER_MAP:
            lexer_name = PYGMENTS_LEXER_MAP[hp]
            results = _pygments_highlight_buffer([line], lexer_name)
            return results[0] if results else Text(line)
        elif hp == HighlightProfile.ENGLISH_TEXT:
            return _highlight_english_line(line, include_markdown=False)
        elif hp == HighlightProfile.ENGLISH_MARKDOWN:
            return _highlight_english_line(line, include_markdown=True)
        else:
            return Text(line)

    def invalidate(self) -> None:
        """Clear the cache, forcing re-highlight on next call."""
        self._cache = None
        self._cache_key = None


def create_highlighter(profile: FileProfile) -> Highlighter:
    """Create a highlighter for the given file profile."""
    return Highlighter(profile)


def highlight_line(line: str, profile: FileProfile) -> Text:
    """One-shot highlight of a single line. For repeated use, prefer Highlighter."""
    h = Highlighter(profile)
    return h.highlight_line(line)


def highlight_buffer(lines: list[str], profile: FileProfile) -> list[Text]:
    """One-shot highlight of an entire buffer."""
    h = Highlighter(profile)
    return h.highlight_buffer(lines)
