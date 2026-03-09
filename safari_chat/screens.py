"""Textual screens for Safari Chat."""

# -----------------------------------------------------------------------
# Textual reserved keys (do not rebind without care):
#   Ctrl+Q   quit (App default, priority)
#   Ctrl+C   copy text / help-quit (App + Screen default)
#   Ctrl+P   command palette (App.COMMAND_PALETTE_BINDING)
#   Tab      focus next widget (Screen default)
#   Shift+Tab focus previous widget (Screen default)
#   Ctrl+I   alias for Tab (terminal limitation)
#   Ctrl+J   alias for Enter (terminal limitation)
#   Ctrl+M   alias for Enter (terminal limitation)
# -----------------------------------------------------------------------

from __future__ import annotations


from textual import events
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import VerticalScroll
from textual.screen import ModalScreen, Screen
from textual.widgets import Static

from safari_chat.engine import plan_response
from safari_chat.state import DistressLevel, SafariChatState

__all__ = [
    "SafariChatHelpScreen",
    "SafariChatMainScreen",
    "SafariChatMemoryScreen",
    "SafariChatOptionsScreen",
    "SafariChatSafetyScreen",
    "SafariChatTopicsScreen",
]

# ---------------------------------------------------------------------------
# CSS (AtariWriter / DOS aesthetic)
# ---------------------------------------------------------------------------

CHAT_CSS = """
Screen {
    background: $background;
    color: $foreground;
    layout: vertical;
}

SafariChatMainScreen {
    background: $background;
    layout: vertical;
}

#chat-distress-bar {
    height: 1;
    background: $primary;
    color: $foreground;
    padding: 0 1;
}

#chat-menu-bar {
    height: 1;
    background: $surface;
    color: $accent;
    padding: 0 1;
}

#chat-transcript {
    height: 1fr;
    padding: 0 1;
}

#chat-input-bar {
    height: 1;
    background: $surface;
    color: $foreground;
    padding: 0 1;
}

#chat-command-bar {
    height: 1;
    background: $primary;
    color: $foreground;
    padding: 0 1;
}

/* Modal screens */
SafariChatTopicsScreen,
SafariChatMemoryScreen,
SafariChatSafetyScreen,
SafariChatOptionsScreen,
SafariChatHelpScreen {
    align: center middle;
}

.modal-container {
    width: 70;
    max-height: 80%;
    border: solid $accent;
    background: $surface;
    padding: 1 2;
}

.modal-title {
    text-align: center;
    text-style: bold;
    color: $accent;
    height: 1;
    margin-bottom: 1;
}

.modal-body {
    height: auto;
    max-height: 100%;
}
"""

# ---------------------------------------------------------------------------
# Distress bar rendering
# ---------------------------------------------------------------------------

_BAR_WIDTH = 10


def _render_distress(level: DistressLevel, score: float) -> str:
    """Render the distress meter as a text bar."""
    filled = int(score * _BAR_WIDTH)
    filled = max(0, min(filled, _BAR_WIDTH))
    bar = "#" * filled + "." * (_BAR_WIDTH - filled)
    return f"DISTRESS: [{bar}] {level.value}"


# ---------------------------------------------------------------------------
# Main chat screen
# ---------------------------------------------------------------------------


class SafariChatMainScreen(Screen):
    """Primary chat interface with distress bar, transcript, and input."""

    CSS = CHAT_CSS

    BINDINGS = [
        Binding("ctrl+q", "quit_chat", "Quit", show=False),
        Binding("ctrl+t", "show_topics", "Topics", show=False),
        Binding("ctrl+s", "show_safety", "Safety", show=False),
        Binding("ctrl+h", "show_help", "Help", show=False),
        Binding("ctrl+m", "show_memory", "Memory", show=False),
        Binding("ctrl+o", "show_options", "Options", show=False),
        Binding("f1", "show_help", "Help", show=False),
        Binding("escape", "quit_chat", "Quit", show=False),
        Binding("pageup", "scroll_up", "PgUp", show=False),
        Binding("pagedown", "scroll_down", "PgDn", show=False),
    ]

    def __init__(self, state: SafariChatState) -> None:
        super().__init__()
        self.state = state
        self._input_buffer: list[str] = []

    def compose(self) -> ComposeResult:
        yield Static(
            _render_distress(self.state.distress_level, self.state.distress_score)
            + "                         SAFARI CHAT v0.1",
            id="chat-distress-bar",
        )
        yield Static(
            " F1 Help | ^T Topics | ^M Memory | ^S Safety | ^O Options | ^Q Quit",
            id="chat-menu-bar",
        )
        yield VerticalScroll(
            Static("Welcome. Type your question below.\n", id="chat-transcript-text"),
            id="chat-transcript",
        )
        yield Static("USER> ", id="chat-input-bar")
        yield Static(
            " F1 Help  ^T Topics  ^M Memory  ^S Safety  ^O Options  ^Q Quit  PgUp/PgDn Scroll",
            id="chat-command-bar",
        )

    # -- Input handling -----------------------------------------------------

    def on_key(self, event: events.Key) -> None:
        if event.key == "enter":
            self._submit_input()
        elif event.key == "backspace":
            if self._input_buffer:
                self._input_buffer.pop()
                self._refresh_input()
        elif (
            event.character
            and len(event.character) == 1
            and event.character.isprintable()
        ):
            self._input_buffer.append(event.character)
            self._refresh_input()

    def _submit_input(self) -> None:
        text = "".join(self._input_buffer).strip()
        self._input_buffer.clear()
        self._refresh_input()
        if not text:
            return

        # Handle slash commands.
        if text.startswith("/"):
            self._handle_slash_command(text)
            return

        _mode, _, _chunk_ids = plan_response(text, self.state)
        self._refresh_transcript()
        self._refresh_distress_bar()

    def _handle_slash_command(self, text: str) -> None:
        cmd = text.lower().strip()
        if cmd == "/topics":
            self.action_show_topics()
        elif cmd == "/help":
            self.action_show_help()
        elif cmd == "/safety":
            self.action_show_safety()
        elif cmd == "/memory":
            self.action_show_memory()
        elif cmd in ("/quit", "/exit"):
            self.action_quit_chat()
        elif cmd == "/clear":
            self.state.conversation.clear()
            self.state.next_node_id = 0
            self.state.distress_score = 0.0
            self.state.distress_level = DistressLevel.LOW
            self._refresh_transcript()
            self._refresh_distress_bar()
        elif cmd.startswith("/options"):
            self.action_show_options()
        else:
            # Unknown command — echo help.
            self.state.add_node(
                "bot", f"Unknown command: {cmd}. Try /help.", intent="system"
            )
            self._refresh_transcript()

    # -- Display refresh ----------------------------------------------------

    def _refresh_input(self) -> None:
        bar = self.query_one("#chat-input-bar", Static)
        bar.update("USER> " + "".join(self._input_buffer))

    def _refresh_distress_bar(self) -> None:
        bar = self.query_one("#chat-distress-bar", Static)
        bar.update(
            _render_distress(self.state.distress_level, self.state.distress_score)
            + "                         SAFARI CHAT v0.1"
        )

    def _refresh_transcript(self) -> None:
        lines: list[str] = []
        for node in self.state.conversation:
            prefix = "USER" if node.speaker == "user" else " BOT"
            lines.append(f"{prefix}> {node.raw_text}")
        content = "\n".join(lines) if lines else "Welcome. Type your question below."
        widget = self.query_one("#chat-transcript-text", Static)
        widget.update(content + "\n")
        # Scroll to bottom.
        scroll = self.query_one("#chat-transcript", VerticalScroll)
        scroll.scroll_end(animate=False)

    # -- Actions ------------------------------------------------------------

    def action_quit_chat(self) -> None:
        if hasattr(self.app, "quit_chat"):
            self.app.quit_chat()  # type: ignore[attr-defined]
        else:
            self.app.exit()

    def action_show_topics(self) -> None:
        self.app.push_screen(SafariChatTopicsScreen(self.state))

    def action_show_safety(self) -> None:
        self.app.push_screen(SafariChatSafetyScreen())

    def action_show_help(self) -> None:
        self.app.push_screen(SafariChatHelpScreen())

    def action_show_memory(self) -> None:
        self.app.push_screen(SafariChatMemoryScreen(self.state))

    def action_show_options(self) -> None:
        self.app.push_screen(SafariChatOptionsScreen(self.state))

    def action_scroll_up(self) -> None:
        scroll = self.query_one("#chat-transcript", VerticalScroll)
        scroll.scroll_up(animate=False)

    def action_scroll_down(self) -> None:
        scroll = self.query_one("#chat-transcript", VerticalScroll)
        scroll.scroll_down(animate=False)


# ---------------------------------------------------------------------------
# Topics modal
# ---------------------------------------------------------------------------


class SafariChatTopicsScreen(ModalScreen[None]):
    """Display parsed topic chunks from the help document."""

    CSS = CHAT_CSS
    BINDINGS = [Binding("escape", "dismiss_modal", "Close")]

    def __init__(self, state: SafariChatState) -> None:
        super().__init__()
        self.state = state

    def compose(self) -> ComposeResult:
        lines: list[str] = ["PARSED TOPICS", "=" * 40, ""]
        if not self.state.chunks:
            lines.append("No help document loaded.")
            lines.append("")
            lines.append("Start Safari Chat with a Markdown file:")
            lines.append("  safari-chat path/to/help.md")
            lines.append("")
            lines.append("The document should be split into sections")
            lines.append("separated by --- lines.")
        else:
            for chunk in self.state.chunks:
                heading = chunk.heading or "(no heading)"
                kw = ", ".join(chunk.keywords[:8]) if chunk.keywords else "-"
                lines.append(f"[{chunk.chunk_id:3d}] {heading}")
                lines.append(f"      Keywords: {kw}")
                lines.append("")
        lines.append("")
        lines.append("Press Escape to close.")
        with VerticalScroll(classes="modal-container"):
            yield Static("TOPICS", classes="modal-title")
            yield Static("\n".join(lines), classes="modal-body")

    def action_dismiss_modal(self) -> None:
        self.dismiss()


# ---------------------------------------------------------------------------
# Memory modal
# ---------------------------------------------------------------------------


class SafariChatMemoryScreen(ModalScreen[None]):
    """Display the conversation tree for debugging / inspection."""

    CSS = CHAT_CSS
    BINDINGS = [Binding("escape", "dismiss_modal", "Close")]

    def __init__(self, state: SafariChatState) -> None:
        super().__init__()
        self.state = state

    def compose(self) -> ComposeResult:
        lines: list[str] = ["CONVERSATION TREE", "=" * 40, ""]
        if not self.state.conversation:
            lines.append("No conversation yet.")
            lines.append("")
            lines.append("Type a message at the USER> prompt")
            lines.append("and press Enter to start chatting.")
            lines.append("")
            lines.append("The conversation tree will appear here,")
            lines.append("showing each turn with speaker, emotion,")
            lines.append("and branch structure.")
        else:
            for node in self.state.conversation:
                indent = "  " * node.branch_depth
                speaker = "USER" if node.speaker == "user" else " BOT"
                text = node.raw_text[:60]
                if len(node.raw_text) > 60:
                    text += "..."
                emo = f" [{node.emotion}]" if node.emotion else ""
                lines.append(f"{indent}#{node.node_id} {speaker}{emo}: {text}")
        lines.append("")
        lines.append("Press Escape to close.")
        with VerticalScroll(classes="modal-container"):
            yield Static("MEMORY", classes="modal-title")
            yield Static("\n".join(lines), classes="modal-body")

    def action_dismiss_modal(self) -> None:
        self.dismiss()


# ---------------------------------------------------------------------------
# Safety modal
# ---------------------------------------------------------------------------


class SafariChatSafetyScreen(ModalScreen[None]):
    """Display safety/crisis policy information."""

    CSS = CHAT_CSS
    BINDINGS = [Binding("escape", "dismiss_modal", "Close")]

    _SAFETY_TEXT = (
        "SAFETY NOTICE\n"
        "=" * 40 + "\n\n"
        "This application is NOT a mental health\n"
        "professional, counselor, or crisis service.\n\n"
        "If you or someone you know is in crisis:\n\n"
        "  * Call emergency services (911 in US)\n"
        "  * Call/text 988 Suicide & Crisis Lifeline\n"
        "  * Text HOME to 741741 (Crisis Text Line)\n"
        "  * Go to nearest emergency room\n"
        "  * Contact a trusted friend or family member\n\n"
        "This bot will attempt to direct you to real\n"
        "help if it detects distress. It will never\n"
        "pretend to be a licensed professional.\n\n"
        "Press Escape to close."
    )

    def compose(self) -> ComposeResult:
        with VerticalScroll(classes="modal-container"):
            yield Static("SAFETY", classes="modal-title")
            yield Static(self._SAFETY_TEXT, classes="modal-body")

    def action_dismiss_modal(self) -> None:
        self.dismiss()


# ---------------------------------------------------------------------------
# Options modal
# ---------------------------------------------------------------------------


class SafariChatOptionsScreen(ModalScreen[None]):
    """Toggle options like synonym variation and retrieval strictness."""

    CSS = CHAT_CSS
    BINDINGS = [
        Binding("escape", "dismiss_modal", "Close"),
        Binding("s", "toggle_synonyms", "Toggle Synonyms"),
    ]

    def __init__(self, state: SafariChatState) -> None:
        super().__init__()
        self.state = state

    def _build_text(self) -> str:
        syn_status = "ON" if self.state.synonym_enabled else "OFF"
        doc = str(self.state.document_path) if self.state.document_path else "(none)"
        chunks = len(self.state.chunks)
        turns = len(self.state.conversation)
        return (
            "OPTIONS\n"
            "=" * 40 + "\n\n"
            f"[S] Synonym Variation: {syn_status}\n\n"
            f"Retrieval Strictness: {self.state.retrieval_strictness:.2f}\n"
            f"Distress Level:       {self.state.distress_level.value}\n"
            f"Distress Score:       {self.state.distress_score:.2f}\n\n"
            "SESSION INFO\n"
            f"  Document: {doc}\n"
            f"  Topics loaded: {chunks}\n"
            f"  Conversation turns: {turns}\n\n"
            "Press Escape to close."
        )

    def compose(self) -> ComposeResult:
        with VerticalScroll(classes="modal-container"):
            yield Static("OPTIONS", classes="modal-title")
            yield Static(self._build_text(), id="options-body", classes="modal-body")

    def action_toggle_synonyms(self) -> None:
        self.state.synonym_enabled = not self.state.synonym_enabled
        self.query_one("#options-body", Static).update(self._build_text())

    def action_dismiss_modal(self) -> None:
        self.dismiss()


# ---------------------------------------------------------------------------
# Help modal
# ---------------------------------------------------------------------------


CHAT_HELP_CONTENT = """\
KEYBOARD SHORTCUTS
  F1 / Ctrl+H      Show this help
  Ctrl+T            Show parsed topics
  Ctrl+M            Show conversation memory
  Ctrl+S            Show safety notice
  Ctrl+O            Show options
  Ctrl+Q / Escape   Quit
  PgUp / PgDn       Scroll transcript
  Enter             Submit message
  Backspace         Delete last character

SLASH COMMANDS
  /topics           List document topics
  /memory           Show conversation tree
  /safety           Show safety notice
  /options          Show options
  /clear            Clear conversation
  /help             Show this help
  /quit             Quit

ABOUT
  Safari Chat is an ELIZA-inspired help
  assistant that retrieves answers from a
  Markdown knowledge document.
  It is NOT an AI or LLM.

TEXTUAL FRAMEWORK (reserved)
  Ctrl+Q            Quit application
  Ctrl+C            Copy text
  Ctrl+P            Command palette\
"""


class SafariChatHelpScreen(ModalScreen[None]):
    """Key commands reference and about text."""

    CSS = CHAT_CSS
    BINDINGS = [Binding("escape", "dismiss_modal", "Close")]

    def compose(self) -> ComposeResult:
        with VerticalScroll(classes="modal-container"):
            yield Static(
                "=== SAFARI CHAT — KEY COMMANDS ===", classes="modal-title"
            )
            yield Static(CHAT_HELP_CONTENT, classes="modal-body")
            yield Static(
                "Press Escape to close",
                classes="modal-body",
            )

    def action_dismiss_modal(self) -> None:
        self.dismiss()
