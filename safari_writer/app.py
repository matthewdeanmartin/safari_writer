"""Safari Writer Textual application."""

from __future__ import annotations

from typing import Any

from pathlib import Path

from textual.app import App, ScreenStackError

import safari_writer.locale_info as _locale_info
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
from safari_writer.screens.print_screen import (
    PrintScreen,
    PrintPreviewScreen,
    TootPreviewScreen,
)
from safari_writer.screens.git_screen import GitPublishScreen
from safari_writer.screens.style_switcher import StyleSwitcherScreen
from safari_writer.screens.doctor import DoctorScreen
from safari_writer.document_io import (
    load_demo_document_buffer,
    load_demo_mail_merge_db,
    load_document_buffer,
    load_sfw_language,
    serialize_document_buffer,
)
from safari_writer.file_types import StorageMode, resolve_file_profile
from safari_writer.format_codec import strip_controls, has_controls, is_sfw
from safari_writer.themes import THEMES, DEFAULT_THEME, load_settings
from safari_writer.autosave import (
    BACKUP_INTERVAL_SECONDS,
    write_backup,
    delete_backup,
)
from safari_writer.screens.backup_screen import BackupScreen
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
from safari_fed.app import build_fed_state
from safari_fed.screens import SafariFedMainScreen
from safari_fed.state import SafariFedState
from safari_repl.screens import ReplMainMenuScreen, ReplEditorScreen
from safari_repl.state import ReplState
from safari_reader.screens import SafariReaderMainMenuScreen
from safari_reader.state import SafariReaderState

__all__ = ["SafariWriterApp"]


def _(s: str) -> str:
    return _locale_info.get_translation().gettext(s)


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
        self.fed_state: SafariFedState | None = None
        self.repl_state: ReplState | None = None
        self.reader_state: SafariReaderState | None = None
        self._fed_compose_active: bool = False
        self._last_backup_path: Path | None = None

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
        self.set_interval(BACKUP_INTERVAL_SECONDS, self._do_autosave)

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
            self.push_screen(GlobalFormatScreen(self.state.fmt, state=self.state))
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
            start = (request.index_path or Path.cwd()).resolve()
            self.dos_state = self._build_safari_dos_state(start)
            self.push_screen(SafariDosBrowserScreen(self.dos_state))
            return
        if destination == "index_external":
            self._action_index_external_via_safari_dos()
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
        if destination == "safari_fed":
            self._action_safari_fed()
            return
        if destination == "safari_repl":
            self._action_safari_repl(request.safari_repl_path)
            return
        if destination == "safari_reader":
            self._action_safari_reader()
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
            self.push_screen(GlobalFormatScreen(self.state.fmt, state=self.state))
        elif action == "mail_merge":
            self.push_screen(MailMergeScreen(self.state))
        elif action == "backup_restore":
            self._action_backup_restore()
        elif action == "index1":
            self._action_index_via_safari_dos()
        elif action == "index2":
            self._action_index_external_via_safari_dos()
        elif action == "safari_base":
            self._action_safari_base()
        elif action == "safari_dos":
            self._action_safari_dos()
        elif action == "safari_chat":
            self._action_safari_chat()
        elif action == "safari_fed":
            self._action_safari_fed()
        elif action == "safari_repl":
            self._action_safari_repl()
        elif action == "safari_reader":
            self._action_safari_reader()
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
        elif action == "doctor":
            self.push_screen(DoctorScreen(doc_language=self.state.doc_language))
        elif action == "quit":
            self._action_quit()

    # ------------------------------------------------------------------
    # Autosave / backup
    # ------------------------------------------------------------------

    def _do_autosave(self) -> None:
        """Periodic backup — only fires when there is modified content."""
        if not self.state.modified:
            return
        try:
            new_path = write_backup(self.state)
        except OSError:
            return
        if new_path is None:
            return
        # Clean up the previous backup for this session now that we have a newer one
        if self._last_backup_path and self._last_backup_path != new_path:
            delete_backup(self._last_backup_path)
        self._last_backup_path = new_path

    def _clear_session_backup(self) -> None:
        """Remove the in-session backup once the user has saved or discarded it."""
        if self._last_backup_path:
            delete_backup(self._last_backup_path)
            self._last_backup_path = None

    def _action_backup_restore(self) -> None:
        self.push_screen(
            BackupScreen(on_resume=self._on_backup_resume),
        )

    def _on_backup_resume(self, backup_path: Path, original_filename: str) -> None:
        """Load a backup into the editor for continued editing."""
        try:
            text = backup_path.read_text(encoding="utf-8")
            self.state.buffer = text.split("\n") if text else [""]
        except OSError as e:
            self.set_message(f"Backup load error: {e}")
            return
        self.state.cursor_row = 0
        self.state.cursor_col = 0
        # Keep original filename hint but mark as unsaved (user must save somewhere new)
        self.state.filename = ""
        self.state.modified = True
        self.state.clear_undo()
        hint = Path(original_filename).name if original_filename else backup_path.stem
        self.set_message(f"Restored backup: {hint}  — use Save As to keep it")
        # Pop the backup screen, then open editor
        try:
            self.pop_screen()
        except Exception:
            pass
        self._open_editor()

    def _action_print(self) -> None:
        self.push_screen(PrintScreen(), callback=self._on_print_choice)

    def _on_print_choice(self, choice: str | None) -> None:
        if choice == "git":
            self.push_screen(GitPublishScreen(document_path=self.state.filename or ""))
        elif choice == "ansi":
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
        elif choice == "mastodon":
            self.post_to_mastodon()
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
        elif choice == "pdf":
            base = self.state.filename
            if base and "." in base:
                base = base.rsplit(".", 1)[0] + ".pdf"
            elif base:
                base += ".pdf"
            else:
                base = "document.pdf"
            self.push_screen(
                FilePromptScreen("Export PDF to", base),
                callback=self._on_export_pdf,
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

    def _on_export_pdf(self, filename: str | None) -> None:
        if not filename:
            return
        try:
            from safari_writer.export_pdf import export_pdf

            pdf_bytes = export_pdf(
                self.state.buffer, self.state.fmt, self.state.mail_merge_db
            )
            Path(filename).write_bytes(pdf_bytes)
            self.set_message(f"Exported PDF: {filename}")
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
                    f"'{name}' has unsaved changes.\nDiscard and create new file?"
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
            # Write a final backup before asking — so if the user chooses to
            # quit, the work is safely in the backup store for later recovery.
            try:
                new_path = write_backup(self.state)
                if new_path:
                    if self._last_backup_path and self._last_backup_path != new_path:
                        delete_backup(self._last_backup_path)
                    self._last_backup_path = new_path
            except OSError:
                pass
            self.push_screen(
                ConfirmScreen(_("Unsaved changes will be lost. Quit?")),
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
                ConfirmScreen(_("Unsaved changes will be lost. Continue?")),
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
        try:
            self.state.mail_merge_db = load_demo_mail_merge_db()
        except Exception:
            pass  # mail merge demo is optional; document still loads
        self.state.cursor_row = 0
        self.state.cursor_col = 0
        self.state.filename = ""
        self.state.modified = False
        self.state.file_profile = resolve_file_profile("demo_document.sfw")
        self.set_message(_("Loaded demo document + mail merge database"))
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
            # Per-document language (i18n Level 1)
            self.state.doc_language = load_sfw_language(document_path)
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
            text = serialize_document_buffer(
                self.state.buffer,
                target_path,
                doc_language=self.state.doc_language,
            )
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
            # Clean up any session backup — document is safely saved
            self._clear_session_backup()
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
            self.set_message(_("No file selected"))
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

    def _action_index_via_safari_dos(self) -> None:
        """Open the safari_dos folder browser for 'Index Current Folder'."""
        start_path = self._picker_start_path()
        self.dos_state = self._build_safari_dos_state(start_path)
        self.push_screen(SafariDosBrowserScreen(self.dos_state))

    def _action_index_external_via_safari_dos(self) -> None:
        """Open the safari_dos devices screen for 'Index External Drive'."""
        self.dos_state = self._build_safari_dos_state(Path.cwd())
        self.push_screen(
            SafariDosDevicesScreen(self.dos_state),
            callback=self._on_choose_device,
        )

    # DEPRECATED: IndexScreen / DrivePickerScreen used to handle index1/index2.
    # Safari DOS browser is now the preferred folder browser for these actions.
    def _action_index_external(self) -> None:
        drives = _find_external_drives()
        if not drives:
            self.set_message(_("No external drives found"))
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

    async def action_quit(self) -> None:
        """Override Textual's default ctrl+q quit.

        If the active screen is a sub-app screen (Chat, DOS), return to the
        menu instead of exiting the whole app.
        """
        if isinstance(self.screen, SafariChatMainScreen):
            self.quit_chat()
            return
        if isinstance(self.screen, SafariFedMainScreen):
            self.quit_fed()
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

    def _action_safari_fed(self) -> None:
        if self.fed_state is None:
            self.fed_state = build_fed_state()
        self.push_screen(SafariFedMainScreen(self.fed_state))

    def quit_fed(self) -> None:
        """Called by SafariFedMainScreen to return to the writer menu."""
        self.pop_screen()

    def _action_safari_reader(self) -> None:
        if self.reader_state is None:
            self.reader_state = SafariReaderState()
        from safari_reader.services import load_library

        load_library(self.reader_state)
        self.push_screen(SafariReaderMainMenuScreen(self.reader_state))

    def quit_reader(self) -> None:
        """Called by SafariReaderMainMenuScreen to return to the writer menu."""
        self.pop_screen()

    def _action_safari_repl(self, bas_path: Path | None = None) -> None:
        if self.repl_state is None:
            self.repl_state = ReplState(loaded_path=bas_path)
        elif bas_path is not None:
            self.repl_state.loaded_path = bas_path
            self.repl_state.output_lines = []
        self.push_screen(ReplMainMenuScreen(self.repl_state))

    def quit_repl(self) -> None:
        """Called by REPL screens to return to the writer menu."""
        self.pop_screen()

    def open_repl(self) -> None:
        """Open the REPL editor screen (called from ReplMainMenuScreen)."""
        if self.repl_state is None:
            self.repl_state = ReplState()
        self.push_screen(ReplEditorScreen(self.repl_state))

    def load_file(self) -> None:
        """Open file picker for the REPL (called from ReplMainMenuScreen)."""
        from safari_repl.app import _FilePickerScreen

        self.push_screen(
            _FilePickerScreen(start_path=Path.cwd()),
            callback=self._on_repl_file_picked,
        )

    def open_help(self) -> None:
        """Open REPL help (called from ReplMainMenuScreen)."""
        from safari_repl.app import _HelpScreen

        self.push_screen(_HelpScreen())

    def request_writer_launch(self, path: Path) -> None:
        """Open a .BAS file from the REPL directly in the writer editor."""
        # Pop REPL screens back to the writer menu, then open in editor
        while isinstance(self.screen, (ReplEditorScreen, ReplMainMenuScreen)):
            self.pop_screen()
        self._on_load_file(str(path))
        self._open_editor()

    def _on_repl_file_picked(self, path: Path | None) -> None:
        if path is None or self.repl_state is None:
            return
        self.repl_state.loaded_path = path
        self.repl_state.output_lines = []
        self.open_repl()

    def open_in_writer_from_text(self, title: str, text: str) -> None:
        """Load Safari Fed text into the editor when it is safe to do so."""

        if self.state.modified:
            self.set_message("Save current document before importing from Safari Fed")
            return
        try:
            current_screen = self.screen
        except ScreenStackError:
            current_screen = None
        if isinstance(current_screen, SafariFedMainScreen):
            self.pop_screen()
        self.state.buffer = text.splitlines() or [""]
        self.state.cursor_row = 0
        self.state.cursor_col = 0
        self.state.filename = ""
        self.state.modified = False
        self.state.file_profile = resolve_file_profile(f"{title}.txt")
        self.state.clear_undo()
        self.set_message(f"Loaded Safari Fed export: {title}")
        self._open_editor()

    def open_fed_compose(
        self,
        reply_to_post: object = None,
        reply: bool = False,
    ) -> None:
        """Open the Safari Writer editor for composing a Mastodon post.

        The editor operates in plain-text / markdown mode.  When the user
        presses Escape the editor returns to Safari Fed instead of the
        main menu.
        """
        from safari_fed.state import FedPost

        lines: list[str] = [""]
        title = "New Mastodon Post"
        if reply and isinstance(reply_to_post, FedPost):
            title = f"Reply to {reply_to_post.handle}"
            lines = [
                f"> {reply_to_post.handle}:",
                *(f"> {line}" for line in reply_to_post.content_lines),
                "",
                f"@{reply_to_post.author} ",
            ]
        self.state.buffer = lines
        self.state.cursor_row = len(lines) - 1
        self.state.cursor_col = len(lines[-1])
        self.state.filename = ""
        self.state.modified = False
        self.state.file_profile = resolve_file_profile(f"{title}.md")
        self.state.clear_undo()
        self._fed_compose_active = True
        self.set_message(
            f"Compose: {title}  |  Ctrl+P to Post/Export  |  Esc to cancel"
        )
        self._open_editor()

    def finish_fed_compose(self) -> None:
        """Return from fed compose editor back to the Safari Fed screen."""
        self._fed_compose_active = False
        self.pop_screen()

    def post_to_mastodon(self) -> None:
        """Show a toot preview screen before posting to Mastodon."""
        if self.fed_state is None:
            self.set_message(_("No Safari Fed session active"))
            return
        text = "\n".join(self.state.buffer).strip()
        if not text:
            self.set_message(_("Cannot post an empty document"))
            return
        account_label = getattr(self.fed_state, "account_label", "unknown")
        from safari_writer.path_utils import leaf_name

        doc_name = self.state.doc_title or (
            leaf_name(self.state.filename) if self.state.filename else ""
        )
        self.push_screen(
            TootPreviewScreen(
                text, account_label, self.state.doc_language, doc_name=doc_name
            ),
            callback=self._on_toot_confirm,
        )

    def _on_toot_confirm(self, confirmed: bool | None) -> None:
        """Actually send the toot after the user confirms from the preview screen."""
        if not confirmed:
            self.set_message(_("Toot cancelled"))
            return
        if self.fed_state is None:
            self.set_message(_("No Safari Fed session active"))
            return
        text = "\n".join(self.state.buffer).strip()
        self.fed_state.compose_lines = text.splitlines()
        message = self.fed_state.send_compose_post()
        self._fed_compose_active = False
        self.set_message(message)

    def _action_safari_base(self) -> None:
        """Open Safari Base with the current mail-merge data."""
        from safari_base.bridge import mail_merge_to_session
        from safari_base.database import ensure_database as ensure_base_database
        from safari_base.screen import SafariBaseScreen

        merge_db = self.state.mail_merge_db
        if merge_db is not None:
            session = mail_merge_to_session(merge_db)
        else:
            session = ensure_base_database()
        self._base_session: Any = session
        self._base_original_merge = merge_db
        self.push_screen(
            SafariBaseScreen(session),
            callback=self._on_safari_base_dismiss,
        )

    def _on_safari_base_dismiss(self, _result: object) -> None:
        """Sync Safari Base edits back to mail-merge state on dismiss."""
        from safari_base.bridge import session_to_mail_merge

        session = getattr(self, "_base_session", None)
        original = getattr(self, "_base_original_merge", None)
        if session is not None:
            self.state.mail_merge_db = session_to_mail_merge(session, original)
        self._base_session = None
        self._base_original_merge = None

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
            self.set_message(_("Load cancelled"))
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
            self.set_message(_("Save cancelled"))
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
            self.set_message(_("Save cancelled"))
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
            self.set_message(_("Delete cancelled"))
            return
        self._on_delete_prompt(str(path))
