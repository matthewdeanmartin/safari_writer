"""Safari Writer Textual application."""

from pathlib import Path

from textual.app import App, ScreenStackError

from safari_writer.cli_types import StartupRequest
from safari_writer.state import AppState
from safari_writer.path_utils import leaf_name
from safari_writer.screens.main_menu import MainMenuScreen
from safari_writer.screens.editor import EditorScreen
from safari_writer.screens.global_format import GlobalFormatScreen
from safari_writer.screens.proofreader import ProofreaderScreen
from safari_writer.screens.mail_merge import MailMergeScreen
from safari_writer.screens.file_ops import FilePromptScreen, ConfirmScreen
from safari_writer.screens.index_screen import IndexScreen, DrivePickerScreen, _find_external_drives
from safari_writer.screens.print_screen import PrintScreen, PrintPreviewScreen
from safari_writer.screens.style_switcher import StyleSwitcherScreen
from safari_writer.document_io import load_demo_document_buffer, load_document_buffer
from safari_writer.format_codec import encode_sfw, strip_controls, has_controls, is_sfw
from safari_writer.themes import THEMES, DEFAULT_THEME, load_settings
from safari_dos.screens import (
    SafariDosBrowserScreen,
    SafariDosDevicesScreen,
    SafariDosGarbageScreen,
    SafariDosMainMenuScreen,
)
from safari_dos.services import (
    list_favorites,
    list_recent_documents,
    list_recent_locations,
    move_to_garbage,
    record_recent_document,
    record_recent_location,
)
from safari_dos.state import SafariDosState

__all__ = ["SafariWriterApp"]


class SafariWriterApp(App):
    """Safari Writer — a UI-compatible clone of AtariWriter 80."""

    TITLE = "Safari Writer"
    # Base CSS removed — all colours come from the active theme via $variables.
    CSS = ""

    def __init__(
        self,
        state: AppState | None = None,
        startup_request: StartupRequest | None = None,
    ) -> None:
        super().__init__()
        self.state = state or AppState()
        self.startup_request = startup_request or StartupRequest()
        self._pending_delete_path: Path | None = None
        self._pending_save_filename = ""
        self._last_safari_dos_path = Path.cwd()
        self.dos_state: SafariDosState | None = None

    def on_mount(self) -> None:
        # Register all themes
        for theme in THEMES.values():
            self.register_theme(theme)

        # Apply saved (or default) theme
        settings = load_settings()
        saved_theme = settings.get("theme", DEFAULT_THEME)
        if saved_theme not in THEMES:
            saved_theme = DEFAULT_THEME
        self.theme = saved_theme

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
            return
        if destination == "safari_dos":
            start_path = request.safari_dos_path or Path.cwd()
            self._last_safari_dos_path = start_path.resolve()
            self.dos_state = self._build_safari_dos_state(start_path.resolve())
            self.push_screen(SafariDosMainMenuScreen(self.dos_state))
            return

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
        elif action == "safari_dos":
            self._action_safari_dos()
        elif action == "load":
            self._action_load_via_safari_dos()
        elif action == "save":
            self._action_save_via_safari_dos()
        elif action == "delete":
            self._action_delete_via_safari_dos()
        elif action == "new_folder":
            self.push_screen(
                FilePromptScreen("New Folder Name"),
                callback=self._on_new_folder,
            )
        elif action == "demo":
            self._action_demo()
        elif action == "style_switcher":
            self.push_screen(StyleSwitcherScreen(self.theme))

    def _action_print(self) -> None:
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
            text = export_markdown(self.state.buffer, self.state.fmt, self.state.mail_merge_db)
            Path(filename).write_text(text, encoding="utf-8")
            self.set_message(f"Exported Markdown: {filename}")
        except OSError as e:
            self.set_message(f"Export error: {e}")

    def _on_export_ps(self, filename: str | None) -> None:
        if not filename:
            return
        try:
            from safari_writer.export_ps import export_postscript
            text = export_postscript(self.state.buffer, self.state.fmt, self.state.mail_merge_db)
            Path(filename).write_text(text, encoding="utf-8")
            self.set_message(f"Exported PostScript: {filename}")
        except OSError as e:
            self.set_message(f"Export error: {e}")

    def _action_create(self) -> None:
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
        self._open_editor()

    def _action_demo(self) -> None:
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
        self.push_screen(EditorScreen(self.state))

    # ------------------------------------------------------------------
    # File operations
    # ------------------------------------------------------------------

    def _on_load_file(self, filename: str | None) -> None:
        if not filename:
            return
        try:
            document_path = Path(filename).resolve()
            self.state.buffer = load_document_buffer(document_path)
            self.state.cursor_row = 0
            self.state.cursor_col = 0
            self.state.filename = str(document_path)
            self.state.modified = False
            fmt_label = "SFW" if is_sfw(filename) else "TXT"
            self._remember_safari_dos_path(document_path.parent)
            record_recent_document(document_path)
            self.set_message(f"Loaded [{fmt_label}]: {document_path}")
        except OSError as e:
            self.set_message(f"Load error: {e}")

    def _on_save_file(self, filename: str | None) -> None:
        if not filename:
            return
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
            target_path = Path(filename).resolve()
            if is_sfw(filename):
                text = encode_sfw(self.state.buffer)
            else:
                text = "\n".join(strip_controls(self.state.buffer))
            target_path.write_text(text, encoding="utf-8")
            self.state.filename = str(target_path)
            self.state.modified = False
            fmt_label = "SFW" if is_sfw(filename) else "TXT"
            self._remember_safari_dos_path(target_path.parent)
            record_recent_document(target_path)
            self.set_message(f"Saved [{fmt_label}]: {target_path}")
        except OSError as e:
            self.set_message(f"Save error: {e}")

    def _on_delete_prompt(self, filename: str | None) -> None:
        if not filename:
            return
        target_path = Path(filename).resolve()
        if not target_path.exists():
            self.set_message(f"File not found: {target_path}")
            return
        self._pending_delete_path = target_path
        self.push_screen(
            ConfirmScreen(f"Move {target_path.name} to Garbage?"),
            callback=self._on_delete_confirm,
        )

    def _on_delete_confirm(self, confirmed: bool | None) -> None:
        if not confirmed:
            self.set_message("Garbage move cancelled")
            return
        if self._pending_delete_path is None:
            self.set_message("No file selected")
            return
        try:
            move_to_garbage(self._pending_delete_path)
            self._remember_safari_dos_path(self._pending_delete_path.parent)
            self.set_message(f"Moved to Garbage: {self._pending_delete_path.name}")
        except (FileNotFoundError, OSError, ValueError) as e:
            self.set_message(f"Garbage error: {e}")

    def _on_new_folder(self, name: str | None) -> None:
        if not name:
            return
        try:
            Path(name).mkdir(exist_ok=True)
            self.set_message(f"Created folder: {name}")
        except OSError as e:
            self.set_message(f"Folder error: {e}")

    def _action_index_external(self) -> None:
        drives = _find_external_drives()
        if not drives:
            self.set_message("No external drives found")
        elif len(drives) == 1:
            self.push_screen(IndexScreen(drives[0], label=f"External: {drives[0]}"))
        else:
            self.push_screen(DrivePickerScreen(drives))

    def set_message(self, msg: str) -> None:
        try:
            screen = self.screen
        except ScreenStackError:
            return
        if hasattr(screen, "set_message"):
            screen.set_message(msg)

    def _action_safari_dos(self) -> None:
        if self._last_safari_dos_path.exists():
            start_path = self._last_safari_dos_path
        elif self.state.filename:
            start_path = Path(self.state.filename).resolve().parent
        else:
            start_path = Path.cwd()
        self.dos_state = self._build_safari_dos_state(start_path.resolve())
        self.push_screen(SafariDosMainMenuScreen(self.dos_state))

    def open_browser(self) -> None:
        if self.dos_state:
            self.push_screen(SafariDosBrowserScreen(self.dos_state))

    def open_devices(self) -> None:
        if self.dos_state:
            self.push_screen(
                SafariDosDevicesScreen(self.dos_state),
                callback=self._on_choose_device,
            )

    def open_garbage(self) -> None:
        self.push_screen(
            SafariDosGarbageScreen(),
            callback=self._on_restore_from_garbage,
        )

    def open_style_switcher(self) -> None:
        self.push_screen(StyleSwitcherScreen(self.theme))

    def quit_dos(self) -> None:
        self.pop_screen()

    def _on_choose_device(self, path: Path | None) -> None:
        if path is None or self.dos_state is None:
            return
        self.dos_state.current_path = path
        self.open_browser()

    def _on_restore_from_garbage(self, restored: Path | None) -> None:
        if restored is None or self.dos_state is None:
            return
        self.dos_state.current_path = restored.parent
        self.open_browser()

    def handle_safari_dos_open(self, path: Path) -> None:
        self._on_load_file(str(path))
        self._open_editor()

    def _build_safari_dos_state(self, start_path: Path) -> SafariDosState:
        resolved = start_path.resolve()
        return SafariDosState(
            current_path=resolved,
            favorites=list_favorites(),
            recent_locations=list_recent_locations(),
            recent_documents=list_recent_documents(),
        )

    def _remember_safari_dos_path(self, path: Path) -> None:
        resolved = path.resolve()
        self._last_safari_dos_path = resolved
        record_recent_location(resolved)

    def _default_save_name(self) -> str:
        if self.state.filename:
            return leaf_name(self.state.filename)
        return "document.sfw" if has_controls(self.state.buffer) else "document.txt"

    def _picker_start_path(self) -> Path:
        if self.state.filename:
            return Path(self.state.filename).resolve().parent
        if self._last_safari_dos_path.exists():
            return self._last_safari_dos_path
        return Path.cwd()

    def _action_load_via_safari_dos(self) -> None:
        self.push_screen(
            SafariDosBrowserScreen(
                self._build_safari_dos_state(self._picker_start_path()),
                picker_mode="file",
            ),
            callback=self._on_choose_load_file,
        )

    def _on_choose_load_file(self, path: Path | None) -> None:
        if path is None:
            self.set_message("Load cancelled")
            return
        self._on_load_file(str(path))
        self._open_editor()

    def _action_save_via_safari_dos(self) -> None:
        self.push_screen(
            FilePromptScreen("Save File Name", self._default_save_name()),
            callback=self._on_choose_save_name,
        )

    def _on_choose_save_name(self, filename: str | None) -> None:
        if not filename:
            self.set_message("Save cancelled")
            return
        self._pending_save_filename = filename
        picker_state = self._build_safari_dos_state(self._picker_start_path())
        picker_state.pending_filename = filename
        self.push_screen(
            SafariDosBrowserScreen(picker_state, picker_mode="directory"),
            callback=self._on_choose_save_location,
        )

    def _on_choose_save_location(self, directory: Path | None) -> None:
        if directory is None:
            self.set_message("Save cancelled")
            return
        self._on_save_file(str(directory / self._pending_save_filename))

    def _action_delete_via_safari_dos(self) -> None:
        self.push_screen(
            SafariDosBrowserScreen(
                self._build_safari_dos_state(self._picker_start_path()),
                picker_mode="file",
            ),
            callback=self._on_choose_delete_file,
        )

    def _on_choose_delete_file(self, path: Path | None) -> None:
        if path is None:
            self.set_message("Delete cancelled")
            return
        self._on_delete_prompt(str(path))
