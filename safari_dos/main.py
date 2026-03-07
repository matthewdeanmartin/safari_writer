"""CLI entrypoint for Safari DOS."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from safari_dos.app import SafariDosApp
from safari_dos.state import SafariDosExitRequest

__all__ = ["build_parser", "main", "parse_args"]


def build_parser() -> argparse.ArgumentParser:
    """Build the Safari DOS CLI parser."""

    parser = argparse.ArgumentParser(
        prog="safari-dos",
        description="Safari DOS file manager.",
        allow_abbrev=False,
    )
    parser.add_argument("path", nargs="?", help="Optional starting directory.")
    return parser


def parse_args(argv: list[str]) -> argparse.Namespace:
    """Parse CLI arguments."""

    return build_parser().parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Launch Safari DOS and process any writer handoff request."""

    args = parse_args(list(sys.argv[1:] if argv is None else argv))
    start_path = Path(args.path).resolve() if args.path else Path.cwd()
    if not start_path.exists():
        raise FileNotFoundError(f"Path not found: {start_path}")
    if not start_path.is_dir():
        raise NotADirectoryError(f"Not a directory: {start_path}")

    app = SafariDosApp(start_path=start_path)
    result = app.run()
    if isinstance(result, SafariDosExitRequest) and result.action == "open-in-writer":
        from safari_writer.main import main as safari_writer_main

        if result.document_path is None:
            return 0
        return safari_writer_main(["tui", "edit", "--file", str(result.document_path)])
    return 0
