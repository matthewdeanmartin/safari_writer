"""CLI entrypoint for Safari REPL."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from safari_repl.app import SafariReplApp
from safari_repl.state import ReplExitRequest

__all__ = ["build_parser", "main", "parse_args"]


def build_parser() -> argparse.ArgumentParser:
    """Build the Safari REPL CLI parser."""

    parser = argparse.ArgumentParser(
        prog="safari-repl",
        description="Safari REPL — Atari BASIC interpreter.",
        allow_abbrev=False,
    )
    parser.add_argument(
        "file",
        nargs="?",
        help="Optional .BAS file to load on startup.",
    )
    return parser


def parse_args(argv: list[str]) -> argparse.Namespace:
    return build_parser().parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Launch Safari REPL and process any writer handoff request."""

    args = parse_args(list(sys.argv[1:] if argv is None else argv))

    bas_path: Path | None = None
    if args.file:
        bas_path = Path(args.file).resolve()
        if not bas_path.exists():
            print(f"File not found: {bas_path}", file=sys.stderr)
            return 2

    app = SafariReplApp(bas_path=bas_path)
    result = app.run()

    if isinstance(result, ReplExitRequest) and result.action == "open-in-writer":
        from safari_writer.main import main as safari_writer_main

        if result.document_path is None:
            return 0
        return safari_writer_main(["tui", "edit", "--file", str(result.document_path)])

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
