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
from safari_writer.screens.index_screen import (
    IndexScreen,
    DrivePickerScreen,
    _find_external_drives,
)
from safari_writer.screens.print_screen import PrintScreen, PrintPreviewScreen
from safari_writer.screens.style_switcher import StyleSwitcherScreen
from safari_writer.document_io import load_demo_document_buffer, load_document_buffer
from safari_writer.file_types import StorageMode, resolve_file_profile
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
from safari_chat.engine import parse_document as parse_chat_document
from safari_chat.screens import SafariChatMainScreen
from safari_chat.state import SafariChatState

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
        if destination == "safari_chat":
            self._action_safari_chat()
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
        elif action == "safari_chat":
            self._action_safari_chat()
        elif action == "load":
            self._action_load_via_safari_dos()
        elif action == "save":
            self._action_save_via_safari_dos()
        elif action == "save_as":
            self._action_save_as()
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
        elif action == "quit":
            self._action_quit()

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

            text = export_markdown(
                self.state.buffer, self.state.fmt, self.state.mail_merge_db
            )
            Path(filename).write_text(text, encoding="utf-8")
            self.set_message(f"Exported Markdown: {filename}")
        except OSError as e:
            self.set_message(f"Export error: {e}")

    def _on_export_ps(self, filename: str | None) -> None:
        if not filename:
            return
        try:
            from safari_writer.export_ps import export_postscript

            text = export_postscript(
                self.state.buffer, self.state.fmt, self.state.mail_merge_db
            )
            Path(filename).write_text(text, encoding="utf-8")
            self.set_message(f"Exported PostScript: {filename}")
        except OSError as e:
            self.set_message(f"Export error: {e}")

    def _action_create(self) -> None:
        has_content = self.state.buffer != [""] or self.state.filename
        if not has_content:
            # Empty buffer with no file — just open editor
            self._do_create()
            return
        if self.state.modified:
            name = leaf_name(self.state.filename) if self.state.filename else "untitled"
            self.push_screen(
                ConfirmScreen(
                    f"'{name}' has unsaved changes.\n"
                    "Discard and create new file?"
                ),
                callback=self._on_create_confirm,
            )
        else:
            name = leaf_name(self.state.filename) if self.state.filename else "document"
            self.push_screen(
                ConfirmScreen(f"Close '{name}' and create new file?"),
                callback=self._on_create_confirm,
            )

    def _on_create_confirm(self, confirmed: bool | None) -> None:
        if confirmed:
            self._do_create()

    def _do_create(self) -> None:
        self.state.buffer = [""]
        self.state.cursor_row = 0
        self.state.cursor_col = 0
        self.state.filename = ""
        self.state.modified = False
        self.state.clear_undo()
        self._open_editor()

    def _action_quit(self) -> None:
        if self.state.modified:
            self.push_screen(
                ConfirmScreen("Unsaved changes will be lost. Quit?"),
                callback=self._on_quit_confirm,
            )
        else:
            self.exit()

    def _on_quit_confirm(self, confirmed: bool | None) -> None:
        if confirmed:
            self.exit()

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
        self.state.file_profile = resolve_file_profile("demo_document.sfw")
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
            # Resolve file profile and sanitize if needed
            self.state.file_profile = resolve_file_profile(document_path.name)
            if self.state.storage_mode == StorageMode.PLAIN and has_controls(
                self.state.buffer
            ):
                self.state.buffer = strip_controls(self.state.buffer)
            profile = self.state.file_profile
            storage = (
                "SFW" if profile.storage_mode == StorageMode.FORMATTED else "PLAIN"
            )
            self._remember_safari_dos_path(document_path.parent)
            record_recent_document(document_path)
            self.set_message(
                f"Loaded [{storage}: {profile.display_name}]: {document_path}"
            )
        except OSError as e:
            self.set_message(f"Load error: {e}")

    def _on_save_file(self, filename: str | None) -> None:
        if not filename:
            return
        if not is_sfw(filename) and has_controls(self.state.buffer):
            self._pending_save_filename = filename
            self.push_screen(
                ConfirmScreen(
                    "Safari Writer formatting is only preserved in .sfw files.\n"
                    "Saving as plain text will remove formatting codes. Continue?"
                ),
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
            # Update file profile for the new filename
            old_profile = self.state.file_profile
            self.state.file_profile = resolve_file_profile(target_path.name)
            new_profile = self.state.file_profile
            # Mode transition: if we went from formatted to plain, normalize the buffer
            if (
                old_profile.storage_mode == StorageMode.FORMATTED
                and new_profile.storage_mode == StorageMode.PLAIN
            ):
                self.state.buffer = strip_controls(self.state.buffer)
                self.set_message(
                    f"Converted document to plain text mode: {target_path}"
                )
            else:
                storage = (
                    "SFW"
                    if new_profile.storage_mode == StorageMode.FORMATTED
                    else "PLAIN"
                )
                self.set_message(f"Saved [{storage}]: {target_path}")
            self._remember_safari_dos_path(target_path.parent)
            record_recent_document(target_path)
            # Update editor highlighter if the editor screen is active
            self._update_editor_highlighter()
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

    def action_quit(self) -> None:
        """Override Textual's default ctrl+q quit.

        If the active screen is a sub-app screen (Chat, DOS), return to the
        menu instead of exiting the whole app.
        """
        if isinstance(self.screen, SafariChatMainScreen):
            self.quit_chat()
            return
        if isinstance(self.screen, (SafariDosMainMenuScreen, SafariDosBrowserScreen)):
            self.quit_dos()
            return
        self._action_quit()

    def _action_safari_chat(self) -> None:
        from safari_chat.app import _DEFAULT_HELP

        doc_path = _DEFAULT_HELP if _DEFAULT_HELP.is_file() else None
        chunks = []
        if doc_path and doc_path.is_file():
            text = doc_path.read_text(encoding="utf-8", errors="replace")
            chunks = parse_chat_document(text)
        self.chat_state = SafariChatState(document_path=doc_path, chunks=chunks)
        self.push_screen(SafariChatMainScreen(self.chat_state))

    def quit_chat(self) -> None:
        """Called by SafariChatMainScreen to return to the writer menu."""
        self.pop_screen()

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

    def _update_editor_highlighter(self) -> None:
        """Tell the active editor to rebuild its highlighter after a profile change."""
        try:
            from safari_writer.screens.editor import EditorArea

            screen = self.screen
            if hasattr(screen, "query_one"):
                editor_area = screen.query_one(EditorArea)
                editor_area.update_highlighter()
        except Exception:
            pass

    def _remember_safari_dos_path(self, path: Path) -> None:
        resolved = path.resolve()
        self._last_safari_dos_path = resolved
        record_recent_location(resolved)

    def _default_save_name(self) -> str:
        if self.state.filename:
            return leaf_name(self.state.filename)
        return ""

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
        # If file already has a name, save directly without prompting
        if self.state.filename:
            target = Path(self.state.filename)
            if target.exists():
                self._on_save_file(self.state.filename)
                return
        # No existing file — fall through to Save As flow
        self._action_save_as()

    def _action_save_as(self) -> None:
        self.push_screen(
            FilePromptScreen("Save File Name", self._default_save_name()),
            callback=self._on_choose_save_name,
        )

    def _on_choose_save_name(self, filename: str | None) -> None:
        if not filename:
            self.set_message("Save cancelled")
            return
        # Default to .sfw extension if none provided
        if "." not in Path(filename).name:
            filename += ".sfw"
        # Check if file already exists and warn
        test_path = self._picker_start_path() / filename
        if test_path.exists():
            self._pending_save_filename = filename
            self.push_screen(
                ConfirmScreen(f"'{filename}' already exists. Overwrite?"),
                callback=self._on_overwrite_confirm,
            )
            return
        self._pending_save_filename = filename
        self._choose_save_location()

    def _on_overwrite_confirm(self, confirmed: bool | None) -> None:
        if confirmed:
            self._choose_save_location()
        else:
            self._action_save_as()

    def _choose_save_location(self) -> None:
        picker_state = self._build_safari_dos_state(self._picker_start_path())
        picker_state.pending_filename = self._pending_save_filename
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
