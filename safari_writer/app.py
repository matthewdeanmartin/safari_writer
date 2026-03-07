"""Safari Writer Textual application."""

from pathlib import Path

from textual.app import App

from safari_writer.cli_types import StartupRequest
from safari_writer.state import AppState
from safari_writer.screens.main_menu import MainMenuScreen
from safari_writer.screens.editor import EditorScreen
from safari_writer.screens.global_format import GlobalFormatScreen
from safari_writer.screens.proofreader import ProofreaderScreen
from safari_writer.screens.mail_merge import MailMergeScreen
from safari_writer.screens.file_ops import FilePromptScreen, ConfirmScreen
from safari_writer.screens.index_screen import IndexScreen, DrivePickerScreen, _find_external_drives
from safari_writer.screens.print_screen import PrintScreen, PrintPreviewScreen
from safari_writer.document_io import load_demo_document_buffer, load_document_buffer
from safari_writer.format_codec import encode_sfw, strip_controls, has_controls, is_sfw

__all__ = ["SafariWriterApp"]


class SafariWriterApp(App):
    """Safari Writer — a UI-compatible clone of AtariWriter 80."""

    TITLE = "Safari Writer"
    CSS = """
    Screen {
        background: #000080;
    }
    """

    def __init__(
        self,
        state: AppState | None = None,
        startup_request: StartupRequest | None = None,
    ) -> None:
        super().__init__()
        self.state = state or AppState()
        self.startup_request = startup_request or StartupRequest()

    def on_mount(self) -> None:
        self.push_screen(MainMenuScreen())
        self._apply_startup_request()

    def _apply_startup_request(self) -> None:
        request = self.startup_request
        destination = request.destination
        if destination == "menu":
            return
        if destination == "edit":
            self._set_initial_cursor(
                request.cursor_line,
                request.cursor_column,
            )
            self._open_editor()
            return
        if destination == "proofreader":
            self.push_screen(
                ProofreaderScreen(
                    self.state,
                    initial_mode=request.proofreader_mode,
                    personal_dict_paths=request.personal_dict_paths,
                )
            )
            return
        if destination == "global_format":
            self.push_screen(GlobalFormatScreen(self.state.fmt))
            return
        if destination == "mail_merge":
            initial_mode = {
                "menu": "main",
                "enter": "enter",
                "update": "update",
                "format": "schema",
                "subset": "subset",
                None: "main",
            }[request.mail_merge_mode]
            self.push_screen(MailMergeScreen(self.state, initial_mode=initial_mode))
            return
        if destination == "print":
            if request.print_target:
                self._on_print_choice(request.print_target)
            else:
                self._action_print()
            return
        if destination == "index_current":
            directory = request.index_path or Path.cwd()
            self.push_screen(IndexScreen(directory, label="Current Folder"))
            return
        if destination == "index_external":
            self._action_index_external()

    def _set_initial_cursor(self, line: int | None, column: int | None) -> None:
        if not self.state.buffer:
            self.state.buffer = [""]
        target_row = max(0, (line or 1) - 1)
        target_row = min(target_row, len(self.state.buffer) - 1)
        target_col = max(0, (column or 1) - 1)
        target_col = min(target_col, len(self.state.buffer[target_row]))
        self.state.cursor_row = target_row
        self.state.cursor_col = target_col

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
        elif action == "demo":
            self._action_demo()

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

    def _action_demo(self) -> None:
        """Load the bundled demo document, prompting if there are unsaved changes."""
        if self.state.modified:
            self.push_screen(
                ConfirmScreen("Unsaved changes will be lost. Continue?"),
                callback=self._on_demo_confirm,
            )
        else:
            self._do_demo()

    def _on_demo_confirm(self, confirmed: bool | None) -> None:
        if confirmed:
            self._do_demo()

    def _do_demo(self) -> None:
        try:
            self.state.buffer = load_demo_document_buffer()
        except (FileNotFoundError, OSError) as e:
            self.set_message(f"Demo load error: {e}")
            return
        self.state.cursor_row = 0
        self.state.cursor_col = 0
        self.state.filename = ""
        self.state.modified = False
        self.set_message("Loaded demo document")
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
            self.state.buffer = load_document_buffer(Path(filename))
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
