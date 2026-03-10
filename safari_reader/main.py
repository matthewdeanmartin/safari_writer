"""CLI entrypoint for Safari Reader."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from safari_reader.app import SafariReaderApp
from safari_reader.state import SafariReaderExitRequest

__all__ = ["build_parser", "main", "parse_args"]


def build_parser() -> argparse.ArgumentParser:
    """Build the Safari Reader CLI parser."""

    parser = argparse.ArgumentParser(
        prog="safari-reader",
        description="Safari Reader — a keyboard-first terminal e-book reader.",
        allow_abbrev=False,
    )
    parser.add_argument(
        "--library",
        help="Path to the local library directory.",
    )
    return parser


def parse_args(argv: list[str]) -> argparse.Namespace:
    """Parse CLI arguments."""

    return build_parser().parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Launch Safari Reader and process any writer handoff request."""

    args = parse_args(list(sys.argv[1:] if argv is None else argv))
    library_dir: Path | None = None
    if args.library:
        library_dir = Path(args.library).resolve()

    app = SafariReaderApp(library_dir=library_dir)
    result = app.run()
    if (
        isinstance(result, SafariReaderExitRequest)
        and result.action == "open-in-writer"
    ):
        from safari_writer.main import main as safari_writer_main

        if result.document_path is None:
            return 0
        return safari_writer_main(["tui", "edit", "--file", str(result.document_path)])
    return 0
