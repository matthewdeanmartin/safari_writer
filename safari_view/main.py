"""
SafariView Main Entry Point.
"""
from __future__ import annotations

import argparse
import logging
from pathlib import Path

from safari_view.ui_terminal.textual_app import SafariViewApp
from safari_view.state import SafariViewState


def main() -> None:
    """Launch the SafariView application."""
    parser = argparse.ArgumentParser(description="SafariView - Retro 8-bit Image Viewer")
    parser.add_argument("path", nargs="?", default=".", help="Initial path to browse")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        )

    state = SafariViewState(current_path=Path(args.path).resolve())
    app = SafariViewApp(state=state)
    app.run()


if __name__ == "__main__":
    main()
