"""Safari Writer Textual application."""

from pathlib import Path

from textual.app import App

from safari_writer.state import AppState
from safari_writer.screens.main_menu import MainMenuScreen
from safari_writer.screens.editor import EditorScreen
from safari_writer.screens.global_format import GlobalFormatScreen
from safari_writer.screens.proofreader import ProofreaderScreen
from safari_writer.screens.mail_merge import MailMergeScreen
from safari_writer.screens.file_ops import FilePromptScreen, ConfirmScreen
from safari_writer.screens.index_screen import IndexScreen, DrivePickerScreen, _find_external_drives
from safari_writer.screens.print_screen import PrintScreen, PrintPreviewScreen
from safari_writer.format_codec import encode_sfw, decode_sfw, strip_controls, has_controls, is_sfw


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
            self.push_screen(ProofreaderScreen(self.state))
        elif action == "print":
            self._action_print()
        elif action == "global_format":
            self.push_screen(GlobalFormatScreen(self.state.fmt))
        elif action == "mail_merge":
            self.push_screen(MailMergeScreen(self.state))
        elif action == "index1":
            self.push_screen(IndexScreen(Path.cwd(), label="Current Folder"))
        elif action == "index2":
            self._action_index_external()
        elif action == "load":
            self.push_screen(
                FilePromptScreen("Load File", self.state.filename),
                callback=self._on_load_file,
            )
        elif action == "save":
            self.push_screen(
                FilePromptScreen("Save File", self.state.filename),
                callback=self._on_save_file,
            )
        elif action == "delete":
            self.push_screen(
                FilePromptScreen("Delete File"),
                callback=self._on_delete_prompt,
            )
        elif action == "new_folder":
            self.push_screen(
                FilePromptScreen("New Folder Name"),
                callback=self._on_new_folder,
            )

    def _action_print(self) -> None:
        """Open the Print/Export dialog."""
        self.push_screen(PrintScreen(), callback=self._on_print_choice)

    def _on_print_choice(self, choice: str | None) -> None:
        if choice == "ansi":
            self.push_screen(PrintPreviewScreen(self.state))
        elif choice == "markdown":
            base = self.state.filename
            if base and "." in base:
                base = base.rsplit(".", 1)[0] + ".md"
            elif base:
                base += ".md"
            else:
                base = "document.md"
            self.push_screen(
                FilePromptScreen("Export Markdown to", base),
                callback=self._on_export_md,
            )
        elif choice == "postscript":
            base = self.state.filename
            if base and "." in base:
                base = base.rsplit(".", 1)[0] + ".ps"
            elif base:
                base += ".ps"
            else:
                base = "document.ps"
            self.push_screen(
                FilePromptScreen("Export PostScript to", base),
                callback=self._on_export_ps,
            )

    def _on_export_md(self, filename: str | None) -> None:
        if not filename:
            return
        try:
            from safari_writer.export_md import export_markdown
            text = export_markdown(self.state.buffer, self.state.fmt)
            Path(filename).write_text(text, encoding="utf-8")
            self.set_message(f"Exported Markdown: {filename}")
        except OSError as e:
            self.set_message(f"Export error: {e}")

    def _on_export_ps(self, filename: str | None) -> None:
        if not filename:
            return
        try:
            from safari_writer.export_ps import export_postscript
            text = export_postscript(self.state.buffer, self.state.fmt)
            Path(filename).write_text(text, encoding="utf-8")
            self.set_message(f"Exported PostScript: {filename}")
        except OSError as e:
            self.set_message(f"Export error: {e}")

    def _action_create(self) -> None:
        """Start a fresh document, prompting if there are unsaved changes."""
        if self.state.modified:
            self.push_screen(
                ConfirmScreen("Unsaved changes will be lost. Continue?"),
                callback=self._on_create_confirm,
            )
        else:
            self._do_create()

    def _on_create_confirm(self, confirmed: bool | None) -> None:
        if confirmed:
            self._do_create()

    def _do_create(self) -> None:
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

    # ------------------------------------------------------------------
    # File operations
    # ------------------------------------------------------------------

    def _on_load_file(self, filename: str | None) -> None:
        if not filename:
            return
        try:
            text = Path(filename).read_text(encoding="utf-8", errors="replace")
            if is_sfw(filename):
                self.state.buffer = decode_sfw(text)
            else:
                self.state.buffer = text.split("\n") if text else [""]
            self.state.cursor_row = 0
            self.state.cursor_col = 0
            self.state.filename = filename
            self.state.modified = False
            fmt_label = "SFW" if is_sfw(filename) else "TXT"
            self.set_message(f"Loaded [{fmt_label}]: {filename}")
        except OSError as e:
            self.set_message(f"Load error: {e}")

    def _on_save_file(self, filename: str | None) -> None:
        if not filename:
            return
        # If saving as plain text and buffer has formatting, warn first
        if not is_sfw(filename) and has_controls(self.state.buffer):
            self._pending_save_filename = filename
            self.push_screen(
                ConfirmScreen("Formatting codes will be stripped (plain text). Continue?"),
                callback=self._on_plain_save_confirm,
            )
            return
        self._do_save(filename)

    def _on_plain_save_confirm(self, confirmed: bool | None) -> None:
        if confirmed:
            self._do_save(self._pending_save_filename)
        else:
            # Re-prompt with .sfw suggestion
            suggested = self._pending_save_filename
            if "." in suggested:
                suggested = suggested.rsplit(".", 1)[0] + ".sfw"
            else:
                suggested += ".sfw"
            self.push_screen(
                FilePromptScreen("Save File", suggested),
                callback=self._on_save_file,
            )

    def _do_save(self, filename: str) -> None:
        try:
            if is_sfw(filename):
                text = encode_sfw(self.state.buffer)
            else:
                text = "\n".join(strip_controls(self.state.buffer))
            Path(filename).write_text(text, encoding="utf-8")
            self.state.filename = filename
            self.state.modified = False
            fmt_label = "SFW" if is_sfw(filename) else "TXT"
            self.set_message(f"Saved [{fmt_label}]: {filename}")
        except OSError as e:
            self.set_message(f"Save error: {e}")

    def _on_delete_prompt(self, filename: str | None) -> None:
        if not filename:
            return
        if not Path(filename).exists():
            self.set_message(f"File not found: {filename}")
            return
        self._pending_delete = filename
        self.push_screen(
            ConfirmScreen(f"Delete {filename}?"),
            callback=self._on_delete_confirm,
        )

    def _on_delete_confirm(self, confirmed: bool | None) -> None:
        if not confirmed:
            self.set_message("Delete cancelled")
            return
        filename = self._pending_delete
        try:
            Path(filename).unlink()
            self.set_message(f"Deleted: {filename}")
        except OSError as e:
            self.set_message(f"Delete error: {e}")

    def _on_new_folder(self, name: str | None) -> None:
        if not name:
            return
        try:
            Path(name).mkdir(exist_ok=True)
            self.set_message(f"Created folder: {name}")
        except OSError as e:
            self.set_message(f"Folder error: {e}")

    def _action_index_external(self) -> None:
        """Show external/removable drives, or message if none found."""
        drives = _find_external_drives()
        if not drives:
            self.set_message("No external drives found")
        elif len(drives) == 1:
            self.push_screen(IndexScreen(drives[0], label=f"External: {drives[0]}"))
        else:
            self.push_screen(DrivePickerScreen(drives))

    def set_message(self, msg: str) -> None:
        """Display a message in the current screen's message bar if available."""
        screen = self.screen
        if hasattr(screen, "set_message"):
            screen.set_message(msg)
