"""CLI runner for the Safari Base dBASE language processor.

Usage:
    python -m safari_base.lang command "USE customers"
    python -m safari_base.lang run myscript.prg
    python -m safari_base.lang repl
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from safari_base.lang.environment import Environment
from safari_base.lang.interpreter import Interpreter


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="safari-base-lang",
        description="Safari Base dBASE III+ language processor",
    )
    parser.add_argument(
        "--work-dir",
        "-w",
        default=".",
        help="Working directory (default: current directory)",
    )
    parser.add_argument(
        "--unsafe",
        action="store_true",
        help="Enable unsafe commands (ZAP, ERASE, RD)",
    )
    parser.add_argument(
        "--sandbox",
        help="Sandbox root directory (paths cannot escape this)",
    )
    sub = parser.add_subparsers(dest="mode")

    cmd_parser = sub.add_parser("command", help="Execute a single command")
    cmd_parser.add_argument("command_text", help="The dBASE command to execute")

    run_parser = sub.add_parser("run", help="Execute a .prg file")
    run_parser.add_argument("program", help="Path to .prg file")

    sub.add_parser("repl", help="Interactive REPL")

    args = parser.parse_args(argv or sys.argv[1:])

    env = Environment(
        work_dir=args.work_dir,
        sandbox=args.sandbox,
        unsafe=args.unsafe,
    )
    interp = Interpreter(env)

    if args.mode == "command":
        result = interp.execute(args.command_text)
        output = env.flush_output()
        if output:
            print(output)
        if result.message and result.message != output:
            print(result.message)
        return 0 if result.success else 1

    if args.mode == "run":
        result = interp.run_program(args.program)
        if result.data:
            print(result.data)
        elif result.message:
            print(result.message)
        return 0 if result.success else 1

    if args.mode == "repl":
        return _repl(interp)

    parser.print_help()
    return 0


def _repl(interp: Interpreter) -> int:
    print("Safari Base dBASE III+ Processor")
    print("Type QUIT to exit.\n")
    while True:
        try:
            line = input(". ")
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not line.strip():
            continue
        result = interp.execute(line)
        output = interp.env.flush_output()
        if output:
            print(output)
        if result.message and result.message != output:
            print(result.message)
        if not result.success:
            print(f"Error: {result.message}")
        if line.strip().upper() == "QUIT":
            break
    interp.env.close_all()
    return 0


if __name__ == "__main__":
    sys.exit(main())
