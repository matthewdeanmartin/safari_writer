"""CLI entrypoint for Safari Fed."""

from __future__ import annotations

import argparse
import sys

from safari_fed.app import SafariFedApp
from safari_fed.state import FOLDER_ORDER, SafariFedExitRequest

__all__ = ["build_parser", "main", "parse_args"]


def build_parser() -> argparse.ArgumentParser:
    """Build the Safari Fed CLI parser."""

    parser = argparse.ArgumentParser(
        prog="safari-fed",
        description="Safari Fed calm Mastodon-style shell.",
        allow_abbrev=False,
    )
    parser.add_argument(
        "--folder",
        choices=FOLDER_ORDER,
        default="Home",
        help="Initial folder to open.",
    )
    parser.add_argument(
        "--account",
        help="Configured Mastodon identity name to open first.",
    )
    return parser


def parse_args(argv: list[str]) -> argparse.Namespace:
    """Parse CLI arguments."""

    return build_parser().parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Launch Safari Fed and process any writer handoff request."""

    args = parse_args(list(sys.argv[1:] if argv is None else argv))
    app = SafariFedApp(start_folder=args.folder, start_account=args.account)
    result = app.run()
    if isinstance(result, SafariFedExitRequest) and result.action == "open-in-writer":
        from safari_writer.main import main as safari_writer_main

        if result.document_path is None:
            return 0
        return safari_writer_main(["tui", "edit", "--file", str(result.document_path)])
    return 0
