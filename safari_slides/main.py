"""CLI entrypoint for Safari Slides."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from safari_slides.app import SafariSlidesApp
from safari_writer.cli_version import version_string

__all__ = ["build_parser", "main", "parse_args"]


def _version_string() -> str:
    return version_string()


def build_parser() -> argparse.ArgumentParser:
    """Build the Safari Slides CLI parser."""

    parser = argparse.ArgumentParser(
        prog="safari-slides",
        description="Safari Slides — a keyboard-first SlideMD viewer.",
        allow_abbrev=False,
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {_version_string()}",
    )
    parser.add_argument(
        "input",
        nargs="?",
        help="Optional SlideMD deck to open (.slides.md or .slidemd).",
    )
    return parser


def parse_args(argv: list[str]) -> argparse.Namespace:
    """Parse CLI arguments."""

    return build_parser().parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Launch Safari Slides."""

    args = parse_args(list(sys.argv[1:] if argv is None else argv))
    source_path: Path | None = None
    if args.input:
        source_path = Path(args.input).resolve()
        if source_path.exists() and source_path.is_dir():
            print(f"Slide deck path is a directory: {source_path}", file=sys.stderr)
            return 2
    app = SafariSlidesApp(source_path=source_path)
    app.run()
    return 0
