"""Safari Writer Textual application."""

from textual.app import App, ComposeResult
from textual.widgets import Static

from safari_writer.state import AppState
from safari_writer.screens.main_menu import MainMenuScreen
from safari_writer.screens.editor import EditorScreen


class SafariWriterApp(App):
    """Safari Writer — a UI-compatible clone of AtariWriter 80."""

    TITLE = "Safari Writer"
    CSS = """
    Screen {
        background: #000080;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self.state = AppState()

    def on_mount(self) -> None:
        self.push_screen(MainMenuScreen())

    # ------------------------------------------------------------------
    # Screen routing from Main Menu
    # ------------------------------------------------------------------

    def handle_menu_action(self, action: str) -> None:
        if action == "create":
            self._action_create()
        elif action == "edit":
            self._action_edit()
        elif action == "verify":
            self.set_message("Proofreader: not yet implemented")
        elif action == "print":
            self.set_message("Print: not yet implemented")
        elif action == "global_format":
            self.set_message("Global Format: not yet implemented")
        elif action == "mail_merge":
            self.set_message("Mail Merge: not yet implemented")
        elif action in ("index1", "index2"):
            drive = action[-1]
            self.set_message(f"Index Drive {drive}: not yet implemented")
        elif action == "load":
            self.set_message("Load File: not yet implemented")
        elif action == "save":
            self.set_message("Save File: not yet implemented")
        elif action == "delete":
            self.set_message("Delete File: not yet implemented")
        elif action == "format_disk":
            self.set_message("Format Disk: not applicable")

    def _action_create(self) -> None:
        """Start a fresh document and open the editor."""
        self.state.buffer = [""]
        self.state.cursor_row = 0
        self.state.cursor_col = 0
        self.state.filename = ""
        self.state.modified = False
        self._open_editor()

    def _action_edit(self) -> None:
        """Return to the active document."""
        self._open_editor()

    def _open_editor(self) -> None:
        # Replace current screen stack with editor, keeping menu beneath
        self.push_screen(EditorScreen(self.state))

    def set_message(self, msg: str) -> None:
        """Display a message in the current screen's message bar if available."""
        screen = self.screen
        if hasattr(screen, "set_message"):
            screen.set_message(msg)
