"""CLI entrypoint for Safari Fed."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from safari_fed.app import SafariFedApp
from safari_fed.client import load_clients_from_env
from safari_fed.opml import (DEFAULT_MAX_ACCOUNTS, DEFAULT_MAX_FEEDS,
                             default_opml_export_path,
                             export_followed_feeds_to_opml)
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
        "command",
        nargs="?",
        choices=("tui", "export-opml"),
        default="tui",
        help="Run the interactive shell or export followed feeds to OPML.",
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
    parser.add_argument(
        "--output",
        help="Destination OPML path for export-opml.",
    )
    parser.add_argument(
        "--max-accounts",
        type=int,
        default=DEFAULT_MAX_ACCOUNTS,
        help="Maximum followed accounts to inspect when exporting OPML.",
    )
    parser.add_argument(
        "--max-feeds",
        type=int,
        default=DEFAULT_MAX_FEEDS,
        help="Maximum feeds to include when exporting OPML.",
    )
    return parser


def parse_args(argv: list[str]) -> argparse.Namespace:
    """Parse CLI arguments."""

    return build_parser().parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Launch Safari Fed and process any writer handoff request."""

    args = parse_args(list(sys.argv[1:] if argv is None else argv))
    if args.command == "export-opml":
        return _handle_export_opml(args)
    app = SafariFedApp(start_folder=args.folder, start_account=args.account)
    result = app.run()
    if isinstance(result, SafariFedExitRequest) and result.action == "open-in-writer":
        from safari_writer.main import main as safari_writer_main

        if result.document_path is None:
            return 0
        return safari_writer_main(["tui", "edit", "--file", str(result.document_path)])
    return 0


def _handle_export_opml(args: argparse.Namespace) -> int:
    """Export discovered followed-profile feeds to an OPML file."""

    clients, default_account = load_clients_from_env()
    if not clients:
        print("No Mastodon credentials found; cannot export OPML.", file=sys.stderr)
        return 2
    account_name = args.account or default_account
    if account_name not in clients:
        available = ", ".join(sorted(clients))
        print(
            f"Unknown Mastodon account '{account_name}'. Available: {available}",
            file=sys.stderr,
        )
        return 2
    output_path = (
        Path(args.output).expanduser().resolve()
        if args.output
        else default_opml_export_path(account_name)
    )
    if args.max_accounts < 1:
        print("--max-accounts must be at least 1", file=sys.stderr)
        return 2
    if args.max_feeds < 1:
        print("--max-feeds must be at least 1", file=sys.stderr)
        return 2
    subscriptions = export_followed_feeds_to_opml(
        clients[account_name],
        output_path,
        max_accounts=args.max_accounts,
        max_feeds=args.max_feeds,
    )
    print(f"Exported {len(subscriptions)} feeds to {output_path}")
    return 0
