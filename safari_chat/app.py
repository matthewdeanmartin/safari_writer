"""Standalone Textual app for Safari Chat."""

from __future__ import annotations

from pathlib import Path

from textual.app import App

from safari_chat.engine import parse_document
from safari_chat.screens import SafariChatMainScreen
from safari_chat.state import SafariChatState

__all__ = ["SafariChatApp"]


class SafariChatApp(App[None]):
    """ELIZA-RAG chat assistant with AtariWriter aesthetic."""

    TITLE = "Safari Chat"

    def __init__(self, document_path: Path | None = None) -> None:
        super().__init__()
        chunks = []
        if document_path and document_path.is_file():
            text = document_path.read_text(encoding="utf-8", errors="replace")
            chunks = parse_document(text)
        self.state = SafariChatState(
            document_path=document_path,
            chunks=chunks,
        )

    def on_mount(self) -> None:
        from safari_writer.themes import THEMES, DEFAULT_THEME, load_settings

        for theme in THEMES.values():
            self.register_theme(theme)
        settings = load_settings()
        saved_theme = settings.get("theme", DEFAULT_THEME)
        if saved_theme not in THEMES:
            saved_theme = DEFAULT_THEME
        self.theme = saved_theme

        self.push_screen(SafariChatMainScreen(self.state))

    def load_document(self, path: Path) -> None:
        """Load or reload a Markdown help document."""
        text = path.read_text(encoding="utf-8", errors="replace")
        self.state.document_path = path
        self.state.chunks = parse_document(text)

    def export_transcript(self, path: Path) -> None:
        """Write the conversation transcript to a file."""
        lines: list[str] = []
        for node in self.state.conversation:
            prefix = "USER" if node.speaker == "user" else " BOT"
            lines.append(f"{prefix}> {node.raw_text}")
        path.write_text("\n".join(lines), encoding="utf-8")
