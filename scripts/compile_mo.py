#!/usr/bin/env python3
"""Pure-Python .po → .mo compiler.  No GNU gettext required.
Usage:
    uv run python scripts/compile_mo.py
Compiles every safari_writer/locales/*/LC_MESSAGES/safari_writer.po
into the corresponding safari_writer.mo binary.
"""

from __future__ import annotations

import array
import os
import re
import struct
from pathlib import Path

MAGIC = 0x950412DE  # little-endian MO magic number


def _parse_po(po_text: str) -> list[tuple[str, str]]:
    """Return list of (msgid, msgstr) pairs from a .po file (simple parser)."""
    pairs: list[tuple[str, str]] = []
    msgid = ""
    msgstr = ""
    in_msgid = False
    in_msgstr = False

    def _unescape(s: str) -> str:
        return s.encode("raw_unicode_escape").decode("unicode_escape")

    header_msgstr = ""
    in_header = False

    for raw_line in po_text.splitlines():
        line = raw_line.strip()
        if line.startswith("#") or not line:
            if in_msgstr:
                if msgid == "" and msgstr:
                    header_msgstr = msgstr
                elif msgid:
                    pairs.append((msgid, msgstr))
                msgid = msgstr = ""
            in_msgid = in_msgstr = False
            in_header = False
            continue
        if line.startswith("msgid "):
            if in_msgstr:
                if msgid == "" and msgstr:
                    header_msgstr = msgstr
                elif msgid:
                    pairs.append((msgid, msgstr))
            msgid = _unescape(line[7:-1])
            msgstr = ""
            in_msgid = True
            in_msgstr = False
            in_header = msgid == ""
        elif line.startswith("msgstr "):
            msgstr = _unescape(line[8:-1])
            in_msgid = False
            in_msgstr = True
        elif line.startswith('"') and line.endswith('"'):
            chunk = _unescape(line[1:-1])
            if in_msgid:
                msgid += chunk
            elif in_msgstr:
                msgstr += chunk

    if in_msgstr:
        if msgid == "" and msgstr:
            header_msgstr = msgstr
        elif msgid:
            pairs.append((msgid, msgstr))

    # Return header entry first (empty msgid), then sorted regular pairs
    result: list[tuple[str, str]] = []
    if header_msgstr:
        result.append(("", header_msgstr))
    result.extend(sorted((m, t) for m, t in pairs if m and t))
    return result


def compile_po(po_path: Path, mo_path: Path) -> None:
    """Compile a single .po file to .mo."""
    po_text = po_path.read_text(encoding="utf-8")
    # _parse_po returns header entry (empty msgid) first, then sorted pairs
    pairs = _parse_po(po_text)

    n = len(pairs)
    # MO format: magic, revision, n, orig_offset, trans_offset, hash_size, hash_offset
    header_size = 7 * 4
    orig_table_offset = header_size
    trans_table_offset = orig_table_offset + n * 8
    strings_offset = trans_table_offset + n * 8

    orig_table: list[tuple[int, int]] = []  # (length, offset) per msgid
    trans_table: list[tuple[int, int]] = []  # (length, offset) per msgstr
    strings = bytearray()

    for msgid, msgstr in pairs:
        encoded_id = msgid.encode("utf-8")
        encoded_str = msgstr.encode("utf-8")
        orig_table.append((len(encoded_id), strings_offset + len(strings)))
        strings += encoded_id + b"\x00"
        trans_table.append((len(encoded_str), strings_offset + len(strings)))
        strings += encoded_str + b"\x00"

    buf = bytearray()

    def pack(*args: int) -> None:
        buf.extend(struct.pack("<" + "I" * len(args), *args))

    pack(MAGIC, 0, n, orig_table_offset, trans_table_offset, 0, strings_offset)
    for length, offset in orig_table:
        pack(length, offset)
    for length, offset in trans_table:
        pack(length, offset)
    buf.extend(strings)

    mo_path.parent.mkdir(parents=True, exist_ok=True)
    mo_path.write_bytes(bytes(buf))
    print(
        f"  compiled {po_path.relative_to(Path.cwd())} -> {mo_path.name}  ({n} messages)"
    )


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    locales_dir = root / "safari_writer" / "locales"
    po_files = sorted(locales_dir.glob("*/LC_MESSAGES/safari_writer.po"))
    if not po_files:
        print("No .po files found under safari_writer/locales/")
        return
    for po_path in po_files:
        mo_path = po_path.with_suffix(".mo")
        compile_po(po_path, mo_path)
    print(f"Done — compiled {len(po_files)} catalog(s).")


if __name__ == "__main__":
    main()
