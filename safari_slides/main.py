"""CLI entrypoint for Safari Slides."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from safari_slides.app import SafariSlidesApp

__all__ = ["build_parser", "main", "parse_args"]


def build_parser() -> argparse.ArgumentParser:
    """Build the Safari Slides CLI parser."""

    parser = argparse.ArgumentParser(
        prog="safari-slides",
        description="Safari Slides — a keyboard-first SlideMD viewer.",
        allow_abbrev=False,
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
        if not source_path.exists():
            print(f"Slide deck not found: {source_path}", file=sys.stderr)
            return 2
    app = SafariSlidesApp(source_path=source_path)
    app.run()
    return 0
