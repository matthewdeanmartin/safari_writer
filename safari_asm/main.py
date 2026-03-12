"""CLI entrypoint for Safari ASM."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from safari_asm.interpreter import SafariAsmRuntimeError, run_source
from safari_asm.parser import SafariAsmParseError

__all__ = ["build_parser", "main", "parse_args"]


def build_parser() -> argparse.ArgumentParser:
    """Build the Safari ASM CLI parser."""

    parser = argparse.ArgumentParser(
        prog="safari-asm",
        description="Safari ASM — assembly-flavored Python interpreter.",
        allow_abbrev=False,
    )
    parser.add_argument(
        "file", nargs="?", help="Optional .ASM file to load on startup."
    )
    parser.add_argument(
        "program_args",
        nargs=argparse.REMAINDER,
        help="Arguments passed through to the Safari ASM program.",
    )
    return parser


def parse_args(argv: list[str]) -> argparse.Namespace:
    """Parse CLI arguments."""

    return build_parser().parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Run a Safari ASM program from a file or stdin."""

    args = parse_args(list(sys.argv[1:] if argv is None else argv))
    program_args = list(args.program_args)
    if program_args and program_args[0] == "--":
        program_args = program_args[1:]

    source_name = "<stdin>"
    if args.file:
        path = Path(args.file).resolve()
        if not path.exists():
            print(f"File not found: {path}", file=sys.stderr)
            return 2
        source = path.read_text(encoding="utf-8")
        source_name = str(path)
    else:
        source = sys.stdin.read()

    try:
        run_source(
            source,
            argv=program_args,
            stdin=sys.stdin,
            stdout=sys.stdout,
            stderr=sys.stderr,
            source_name=source_name,
        )
    except (SafariAsmParseError, SafariAsmRuntimeError) as exc:
        print(exc, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
