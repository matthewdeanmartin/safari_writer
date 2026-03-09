"""Encode/decode Safari Writer formatted files (.sfw).

The .sfw format represents internal control characters as human-readable
backslash-escaped tags.  Files are valid UTF-8 and can be viewed in any
text editor.

Plain-text files use no encoding — control characters are stripped on save.
"""

from __future__ import annotations

import re as _re

__all__ = [
    "decode_sfw",
    "encode_sfw",
    "extract_sfw_metadata",
    "has_controls",
    "inject_sfw_metadata",
    "is_sfw",
    "strip_controls",
]

# Internal control bytes → .sfw tag (without the leading backslash)
_ENCODE_MAP: dict[str, str] = {
    "\x01": "B",  # bold toggle
    "\x02": "U",  # underline toggle
    "\x03": "C",  # center line
    "\x04": "R",  # flush right
    "\x05": "G",  # elongated toggle
    "\x06": "^",  # superscript toggle
    "\x07": "v",  # subscript toggle
    "\x10": "P",  # paragraph indent mark
    "\x11": "@",  # mail merge field
    "\x12": "H:",  # header line marker
    "\x13": "F:",  # footer line marker
    "\x14": "S",  # section heading
    "\x15": "E",  # hard page break
    "\x16": ">",  # chain print file
    "\x17": "_",  # form printing blank
}

# Reverse: tag suffix → internal byte
_DECODE_MAP: dict[str, str] = {v: k for k, v in _ENCODE_MAP.items()}

# All control bytes we use (for stripping)
_CONTROL_CHARS = set(_ENCODE_MAP.keys())


def encode_sfw(buffer: list[str]) -> str:
    """Encode a document buffer to .sfw file text.

    Escapes literal backslashes first, then replaces each control byte
    with its ``\\TAG`` form.
    """
    lines: list[str] = []
    for line in buffer:
        out: list[str] = []
        for ch in line:
            if ch == "\\":
                out.append("\\\\")
            elif ch in _ENCODE_MAP:
                out.append("\\" + _ENCODE_MAP[ch])
            else:
                out.append(ch)
        lines.append("".join(out))
    return "\n".join(lines)


def decode_sfw(text: str) -> list[str]:
    """Decode .sfw file text back into a buffer with internal control bytes.

    Recognised ``\\TAG`` sequences become control bytes.
    ``\\\\`` becomes a literal backslash.
    Unrecognised ``\\X`` sequences are left as-is for forward-compat.
    """
    buffer: list[str] = []
    for raw_line in text.split("\n"):
        out: list[str] = []
        i = 0
        n = len(raw_line)
        while i < n:
            ch = raw_line[i]
            if ch == "\\" and i + 1 < n:
                # Try two-char tags first (e.g. "H:", "F:")
                two = raw_line[i + 1 : i + 3]
                if two in _DECODE_MAP:
                    out.append(_DECODE_MAP[two])
                    i += 3
                    continue
                # Single-char tags
                one = raw_line[i + 1]
                if one == "\\":
                    out.append("\\")
                    i += 2
                    continue
                if one in _DECODE_MAP:
                    out.append(_DECODE_MAP[one])
                    i += 2
                    continue
                # Unrecognised escape — leave as-is
                out.append(ch)
                i += 1
            else:
                out.append(ch)
                i += 1
        buffer.append("".join(out))
    return buffer if buffer else [""]


def strip_controls(buffer: list[str]) -> list[str]:
    """Return a copy of the buffer with all control characters removed."""
    return ["".join(ch for ch in line if ch not in _CONTROL_CHARS) for line in buffer]


def has_controls(buffer: list[str]) -> bool:
    """Check whether the buffer contains any formatting control characters."""
    for line in buffer:
        for ch in line:
            if ch in _CONTROL_CHARS:
                return True
    return False


def is_sfw(filename: str) -> bool:
    """Check if a filename uses the .sfw extension."""
    return filename.lower().endswith(".sfw")


# ---------------------------------------------------------------------------
# Metadata header helpers  (i18n Level 1)
# ---------------------------------------------------------------------------

_META_RE = _re.compile(r"^%%(\w+):\s*(.+)$")


def extract_sfw_metadata(text: str) -> tuple[dict[str, str], str]:
    """Extract ``%%key: value`` header lines from raw .sfw file text.

    Returns ``(metadata_dict, remaining_text)`` where *remaining_text* has
    the header lines stripped.
    """
    meta: dict[str, str] = {}
    lines = text.split("\n")
    body_start = 0
    for i, line in enumerate(lines):
        m = _META_RE.match(line)
        if m:
            meta[m.group(1)] = m.group(2).strip()
            body_start = i + 1
        else:
            break
    remaining = "\n".join(lines[body_start:])
    return meta, remaining


def inject_sfw_metadata(metadata: dict[str, str], body: str) -> str:
    """Prepend ``%%key: value`` header lines to encoded .sfw body text."""
    if not metadata:
        return body
    header = "\n".join(f"%%{k}: {v}" for k, v in sorted(metadata.items()))
    return header + "\n" + body
