"""CLI entrypoint for Safari Base."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from safari_base.app import SafariBaseApp

__all__ = ["build_parser", "main", "parse_args"]


def build_parser() -> argparse.ArgumentParser:
    """Build the Safari Base CLI parser."""

    parser = argparse.ArgumentParser(
        prog="safari-base",
        description="Safari Base dBASE-style shell.",
        allow_abbrev=False,
    )
    parser.add_argument("database", nargs="?", help="Optional SQLite database path.")
    return parser


def parse_args(argv: list[str]) -> argparse.Namespace:
    """Parse CLI arguments."""

    return build_parser().parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Launch Safari Base."""

    args = parse_args(list(sys.argv[1:] if argv is None else argv))
    database_path = Path(args.database).resolve() if args.database else None
    if database_path is not None and database_path.exists() and database_path.is_dir():
        raise NotADirectoryError(f"Not a database file: {database_path}")

    app = SafariBaseApp(database_path=database_path)
    app.run()
    return 0
