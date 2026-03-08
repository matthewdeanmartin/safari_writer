"""CLI entrypoint for Safari Chat."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from safari_chat.app import SafariChatApp

__all__ = ["build_parser", "main", "parse_args"]


def build_parser() -> argparse.ArgumentParser:
    """Build the Safari Chat CLI parser."""

    parser = argparse.ArgumentParser(
        prog="safari-chat",
        description="Safari Chat — ELIZA-style help assistant.",
        allow_abbrev=False,
    )
    parser.add_argument(
        "document",
        nargs="?",
        help="Path to a Markdown help document (optional).",
    )
    return parser


def parse_args(argv: list[str]) -> argparse.Namespace:
    """Parse CLI arguments."""

    return build_parser().parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Launch Safari Chat."""

    args = parse_args(list(sys.argv[1:] if argv is None else argv))
    doc_path: Path | None = None
    if args.document:
        doc_path = Path(args.document).resolve()
        if not doc_path.is_file():
            print(f"Error: document not found: {doc_path}", file=sys.stderr)
            return 1

    app = SafariChatApp(document_path=doc_path)
    app.run()
    return 0
