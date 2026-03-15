"""Textual screens for Safari Fed (Mastodon) and Safari Feed (RSS)."""

from __future__ import annotations

from datetime import datetime
from textwrap import shorten, wrap

from textual import events, work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal
from textual.events import Key
from textual.screen import ModalScreen, Screen
from textual.timer import Timer
from textual.widgets import Static

from safari_fed.feed_state import FeedRecord, SafariFeedState
from safari_fed.opml import (
    DEFAULT_MAX_ACCOUNTS,
    DEFAULT_MAX_FEEDS,
    default_opml_export_path,
    export_followed_feeds_to_opml,
)
from safari_fed.services import (
    fetch_article,
    fetch_feed,
    load_feed_preferences,
    parse_opml_document,
    render_entry_source,
    save_feed_preferences,
    scan_opml_documents,
)
from safari_fed.state import (
    FOLDER_ORDER,
    FedPost,
    SafariFedState,
    render_post_for_writer,
    render_thread_for_writer,
)

__all__ = [
    "FED_CSS",
    "FedHelpScreen",
    "FedOpmlLimitsScreen",
    "SafariFedMainScreen",
    "SafariFeedListScreen",
    "SafariFeedMainScreen",
    "SafariFeedReaderScreen",
]


# =====================================================================
# Safari Fed — Mastodon client screens
# =====================================================================

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

FED_HELP_CONTENT = """\
NAVIGATION
  J / Down          Next post             K / Up            Previous post
  PageDown          Skip 5 posts          PageUp            Skip 5 posts
  Enter             Open reader view      T                 Open thread view
  Esc               Back to index / Quit  Q                 Quit / Back

FOLDERS
  Tab / Shift+Tab   Cycle folders         H                 Home folder
  N                 Mentions folder       G                 Next folder

ACTIONS
  C                 Compose new post      R                 Reply to post
  B                 Boost post            F                 Favourite post
  M                 Toggle bookmark       X                 Toggle read/unread
  D                 Toggle deferred       U                 Sync from Mastodon
  W                 Export to Writer      O                 Export OPML feeds
  ~                 Run macro → Draft

ACCOUNTS
  A                 Cycle account         1-9               Select account

OTHER
  F1 / ?            This help screen      Ctrl+Q            Quit Safari Fed

TEXTUAL FRAMEWORK (reserved)
  Ctrl+Q            Quit application      Ctrl+C            Copy text
  Ctrl+P            Command palette       Tab/Shift+Tab     Focus widgets\
"""

FED_HELP_CSS = """
FedHelpScreen {
    align: center middle;
}

#fed-help-dialog {
    width: 80;
    height: 28;
    border: solid $primary;
    background: $surface;
    padding: 1 2;
}

#fed-help-title {
    text-align: center;
    text-style: bold;
    color: $accent;
    margin-bottom: 1;
}

#fed-help-content {
    height: 1fr;
    color: $foreground;
}

#fed-help-footer {
    text-align: center;
    color: $text-muted;
    margin-top: 1;
}
"""


class FedHelpScreen(ModalScreen):
    """Full key-command reference for Safari Fed."""

    CSS = FED_HELP_CSS

    def compose(self) -> ComposeResult:
        with Container(id="fed-help-dialog"):
            yield Static("=== SAFARI FED — KEY COMMANDS ===", id="fed-help-title")
            yield Static(FED_HELP_CONTENT, id="fed-help-content")
            yield Static("Press any key to close", id="fed-help-footer")

    def on_key(self, event: events.Key) -> None:
        self.dismiss()


FED_LIMITS_CSS = """
FedOpmlLimitsScreen {
    align: center middle;
}

#fed-limits-dialog {
    width: 56;
    height: 12;
    border: solid $primary;
    background: $surface;
    padding: 1 2;
}

#fed-limits-title {
    text-align: center;
    text-style: bold;
    color: $accent;
}

.fed-limits-line {
    margin-top: 1;
}

#fed-limits-hint {
    color: $text-muted;
    text-align: center;
    margin-top: 1;
}
"""


class FedOpmlLimitsScreen(ModalScreen[tuple[int, int] | None]):
    """Prompt for bounded OPML export limits."""

    CSS = FED_LIMITS_CSS

    def __init__(
        self,
        max_accounts: int = DEFAULT_MAX_ACCOUNTS,
        max_feeds: int = DEFAULT_MAX_FEEDS,
    ) -> None:
        super().__init__()
        self._accounts_buf = str(max_accounts)
        self._feeds_buf = str(max_feeds)
        self._active_field = 0

    def compose(self) -> ComposeResult:
        with Container(id="fed-limits-dialog"):
            yield Static("=== OPML EXPORT LIMITS ===", id="fed-limits-title")
            yield Static("", id="fed-limits-accounts", classes="fed-limits-line")
            yield Static("", id="fed-limits-feeds", classes="fed-limits-line")
            yield Static(
                "Tab switch fields | Enter export | Esc cancel",
                id="fed-limits-hint",
            )

    def on_mount(self) -> None:
        self._refresh_inputs()

    def _render_field(self, label: str, value: str, active: bool) -> str:
        cursor = "[reverse] [/reverse]" if active else ""
        return f"{label}: {value}{cursor}"

    def _refresh_inputs(self) -> None:
        self.query_one("#fed-limits-accounts", Static).update(
            self._render_field(
                "Accounts to check (max)",
                self._accounts_buf,
                self._active_field == 0,
            )
        )
        self.query_one("#fed-limits-feeds", Static).update(
            self._render_field(
                "RSS feeds to find (max)",
                self._feeds_buf,
                self._active_field == 1,
            )
        )

    def on_key(self, event: events.Key) -> None:
        if event.key == "escape":
            self.dismiss(None)
            event.stop()
            return
        if event.key == "tab":
            self._active_field = (self._active_field + 1) % 2
            self._refresh_inputs()
            event.stop()
            return
        if event.key == "shift+tab":
            self._active_field = (self._active_field - 1) % 2
            self._refresh_inputs()
            event.stop()
            return
        if event.key == "enter":
            try:
                max_accounts = int(self._accounts_buf.strip())
                max_feeds = int(self._feeds_buf.strip())
            except ValueError:
                self.notify("Enter whole numbers for both limits", severity="error")
                event.stop()
                return
            if max_accounts < 1 or max_feeds < 1:
                self.notify("Both limits must be at least 1", severity="error")
                event.stop()
                return
            self.dismiss((max_accounts, max_feeds))
            event.stop()
            return
        if event.key == "backspace":
            if self._active_field == 0:
                self._accounts_buf = self._accounts_buf[:-1]
            else:
                self._feeds_buf = self._feeds_buf[:-1]
            self._refresh_inputs()
            event.stop()
            return
        if event.character and event.character.isdigit():
            if self._active_field == 0:
                self._accounts_buf += event.character
            else:
                self._feeds_buf += event.character
            self._refresh_inputs()
            event.stop()
            return
        event.stop()


FED_CSS = """
Screen {
    background: $background;
    color: $foreground;
    min-width: 140;
}

SafariFedMainScreen {
    background: $background;
    layout: vertical;
}

#fed-title {
    height: 1;
    background: $primary;
    color: $foreground;
    padding: 0 1;
}

#fed-folders {
    height: 1;
    background: $secondary;
    color: $foreground;
    padding: 0 1;
}

#fed-accounts {
    height: 1;
    background: $panel;
    color: $foreground;
    padding: 0 1;
}

#fed-body {
    width: 1fr;
    height: 1fr;
    border: solid $accent;
    background: $surface;
    layout: horizontal;
}

#fed-sidebar {
    width: 100;
    min-width: 90;
    height: 1fr;
    border-right: solid $accent;
    layout: vertical;
}

#fed-main {
    width: 1fr;
    min-width: 56;
    height: 1fr;
    layout: vertical;
}

#fed-sidebar-title,
#fed-detail-title {
    height: 1;
    background: $panel;
    color: $foreground;
    padding: 0 1;
}

#fed-index,
#fed-detail {
    height: 1fr;
    padding: 0 1;
    color: $foreground;
}

#fed-command {
    height: 1;
    background: $surface;
    color: $accent;
    padding: 0 1;
}

#fed-status {
    height: 1;
    background: $primary;
    color: $foreground;
    padding: 0 1;
}
"""


_SPINNER_FRAMES = ("⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏")


class SafariFedMainScreen(Screen[None]):
    """Single-screen retro fediverse shell."""

    CSS = FED_CSS

    def __init__(self, state: SafariFedState) -> None:
        super().__init__()
        self.state = state
        self._spinner_frame: int = 0
        self._spinner_active: bool = False
        self._spinner_timer: Timer | None = None

    def compose(self) -> ComposeResult:
        yield Static("", id="fed-title")
        yield Static("", id="fed-folders")
        yield Static("", id="fed-accounts")
        with Horizontal(id="fed-body"):
            with Container(id="fed-sidebar"):
                yield Static("", id="fed-sidebar-title")
                yield Static("", id="fed-index")
            with Container(id="fed-main"):
                yield Static("", id="fed-detail-title")
                yield Static("", id="fed-detail")
        yield Static("", id="fed-command")
        yield Static("", id="fed-status")

    def on_mount(self) -> None:
        self._refresh()

    def _start_spinner(self) -> None:
        if self._spinner_active:
            return
        self._spinner_active = True
        self._spinner_frame = 0
        self._spinner_timer = self.set_interval(0.1, self._tick_spinner)

    def _stop_spinner(self) -> None:
        self._spinner_active = False
        if self._spinner_timer is not None:
            self._spinner_timer.stop()
            self._spinner_timer = None
        self._refresh_title()

    def _tick_spinner(self) -> None:
        self._spinner_frame = (self._spinner_frame + 1) % len(_SPINNER_FRAMES)
        self._refresh_title()

    def _refresh_title(self) -> None:
        try:
            self.query_one("#fed-title", Static).update(self._render_title())
        except Exception:
            pass

    def set_message(self, message: str) -> None:
        """Update the status message."""

        self.state.status_message = message
        self._refresh_status()

    def on_key(self, event: events.Key) -> None:
        if self.state.view_mode == "compose" and self._handle_compose_key(event):
            return
        key = event.key
        if key == "ctrl+q":
            self._quit_fed()
            return
        if key == "a":
            self.set_message(self.state.cycle_account(1))
            self._refresh()
            self._persist_state()
            return
        if key.isdigit() and key != "0":
            self.set_message(self.state.select_account_by_number(int(key)))
            self._refresh()
            self._persist_state()
            return
        if key in {"up", "k"}:
            self.state.move_selection(-1)
            self._refresh()
            return
        if key in {"down", "j"}:
            self.state.move_selection(1)
            self._refresh()
            return
        if key == "pageup":
            self.state.move_selection(-5)
            self._refresh()
            return
        if key == "pagedown":
            self.state.move_selection(5)
            self._refresh()
            return
        if key == "tab":
            self.state.cycle_folder(1)
            self._refresh()
            return
        if key == "shift+tab":
            self.state.cycle_folder(-1)
            self._refresh()
            return
        if key == "h":
            self.state.set_folder("Home")
            self._refresh()
            return
        if key == "n":
            self.state.set_folder("Mentions")
            self._refresh()
            return
        if key == "g":
            self.state.cycle_folder(1)
            self._refresh()
            return
        if key == "enter":
            if self.state.current_post() is not None:
                self.state.view_mode = "reader"
                self.set_message("Opened post reader")
                self._refresh()
            return
        if key == "escape":
            if self.state.view_mode != "index":
                self.state.view_mode = "index"
                self.set_message("Returned to timeline index")
                self._refresh()
                return
            self._quit_fed()
            return
        if key == "q":
            if self.state.view_mode == "index":
                self._quit_fed()
            else:
                self.state.view_mode = "index"
                self.set_message("Returned to timeline index")
                self._refresh()
            return
        if key == "t":
            if self.state.current_post() is not None:
                self.state.view_mode = "thread"
                self.set_message("Opened thread tree")
                self._refresh()
            return
        if key == "c":
            self._start_compose()
            return
        if key == "r":
            self._start_compose(reply=True)
            return
        if key == "m":
            post = self.state.toggle_bookmark()
            if post is not None:
                verb = "Bookmarked" if post.bookmarked else "Removed bookmark"
                self.set_message(f"{verb}: {post.handle}")
            else:
                self.set_message(self.state.status_message)
            self._refresh()
            return
        if key == "x":
            post = self.state.toggle_read()
            if post is not None:
                verb = "Marked unread" if post.unread else "Marked read"
                self.set_message(f"{verb}: {post.handle}")
                self._refresh()
            return
        if key == "d":
            post = self.state.toggle_deferred()
            if post is not None:
                verb = "Deferred" if post.deferred else "Restored"
                self.set_message(f"{verb}: {post.handle}")
                self._refresh()
            return
        if key == "b":
            self.set_message(self.state.boost_current())
            self._refresh()
            return
        if key == "f":
            self.set_message(self.state.favourite_current())
            self._refresh()
            return
        if key == "u":
            self._sync_in_background()
            return
        if key == "w":
            self._open_in_writer()
            return
        if key == "o":
            self._prompt_for_opml_export()
            return
        if key in {"f1", "question_mark"}:
            self.app.push_screen(FedHelpScreen())
            return
        if key == "slash":
            self.set_message("Search shell not wired yet")
        if key == "tilde":
            self._run_macro()

    def _handle_compose_key(self, event: events.Key) -> bool:
        key = event.key
        if key == "ctrl+x":
            self._send_compose()
            return True
        if key == "ctrl+s":
            self._save_draft()
            return True
        if key in {"ctrl+c", "escape"}:
            self.state.view_mode = "index"
            self.set_message("Compose cancelled")
            self._refresh()
            return True
        if key == "backspace":
            line = self.state.compose_lines[-1]
            if line:
                self.state.compose_lines[-1] = line[:-1]
            elif len(self.state.compose_lines) > 1:
                tail = self.state.compose_lines.pop()
                self.state.compose_lines[-1] += tail
            self._refresh()
            return True
        if key == "enter":
            self.state.compose_lines.append("")
            self._refresh()
            return True
        if (
            event.character
            and len(event.character) == 1
            and event.character.isprintable()
        ):
            self.state.compose_lines[-1] += event.character
            self._refresh()
            return True
        return False

    def _start_compose(self, reply: bool = False) -> None:
        post = self.state.current_post()
        # Set reply context on the state so send_compose_post knows the target
        self.state.reply_to_id = post.post_id if reply and post is not None else None
        self.state.compose_visibility = "Public"
        self.state.compose_cw = "none"
        # If running inside Safari Writer, open the full editor
        if hasattr(self.app, "open_fed_compose"):
            self.app.open_fed_compose(
                reply_to_post=post if reply else None,
                reply=reply,
            )
            return
        # Fallback: built-in mini compose
        self.state.view_mode = "compose"
        self.state.compose_lines = [f"@{post.author} " if reply and post else ""]
        target = post.handle if reply and post is not None else "timeline"
        self.set_message(f"Compose opened for {target}")
        self._refresh()

    def _save_draft(self) -> None:
        text = "\n".join(self.state.compose_lines).strip()
        if not text:
            self.set_message("Draft is empty")
            return
        draft = self.state.create_local_post(text=text, draft=True)
        self.state.view_mode = "index"
        self.state.set_folder("Drafts")
        self.state.focus_post(draft.post_id)
        self.set_message("Draft saved locally")
        self._refresh()

    def _send_compose(self) -> None:
        self.set_message(self.state.send_compose_post())
        self._refresh()

    def _run_macro(self) -> None:
        """Open the macro picker and run the selected .BAS file against the current post."""
        from safari_basic.runner import MacroRunner
        from safari_writer.screens.macro_picker import MacroPickerScreen

        post = self.state.current_post()
        context = MacroRunner.build_context(
            document_lines=[],
            cursor_row=0,
            cursor_col=0,
            current_post=post,
        )

        def _on_picked(path: object) -> None:
            from pathlib import Path as _Path

            if not isinstance(path, _Path):
                self.set_message("Macro cancelled")
                return
            output, error = MacroRunner.run(path, context)
            if error:
                self.set_message(error)
                self._refresh()
                return
            if not output:
                self.set_message(f"Macro ran: {path.stem} (no output)")
                self._refresh()
                return
            draft = self.state.create_local_post(text=output, draft=True)
            self.state.set_folder("Drafts")
            self.state.focus_post(draft.post_id)
            self.set_message(f"Macro: {path.stem} — saved as draft")
            self._refresh()

        self.app.push_screen(MacroPickerScreen(), _on_picked)

    def _prompt_for_opml_export(self) -> None:
        """Ask for bounded OPML export limits before starting."""
        self.app.push_screen(FedOpmlLimitsScreen(), self._on_opml_limits_selected)

    def _on_opml_limits_selected(
        self, result: tuple[int, int] | None
    ) -> None:
        """Start OPML export if the user confirmed limits."""
        if result is None:
            self.set_message("OPML export cancelled")
            return
        max_accounts, max_feeds = result
        self._export_opml_in_background(max_accounts=max_accounts, max_feeds=max_feeds)

    def _export_opml_in_background(
        self, max_accounts: int, max_feeds: int
    ) -> None:
        """Start followed-feed OPML export in a worker thread."""
        if self.state.client is None:
            self.set_message("No Mastodon credentials found; cannot export OPML")
            return
        self._start_spinner()
        self.set_message("Exporting OPML…")
        self._do_export_opml_worker(max_accounts, max_feeds)

    @work(thread=True, exclusive=True)
    def _do_export_opml_worker(self, max_accounts: int, max_feeds: int) -> None:
        """Worker: discover followed feeds and write the OPML file."""
        try:
            account_name = getattr(self.state.client, "account_name", "safari-fed")
            output_path = default_opml_export_path(account_name)
            subscriptions = export_followed_feeds_to_opml(
                self.state.client,
                output_path=output_path,
                max_accounts=max_accounts,
                max_feeds=max_feeds,
            )
            message = f"OPML exported: {len(subscriptions)} feeds → {output_path}"
        except Exception as error:
            message = f"OPML export error: {error}"
        self.app.call_from_thread(self._on_export_opml_done, message)

    def _on_export_opml_done(self, message: str) -> None:
        """Called on the main thread after OPML export completes."""
        self._stop_spinner()
        self.set_message(message)
        self._refresh()

    def _open_in_writer(self) -> None:
        post = self.state.current_post()
        if post is None:
            self.set_message("No post selected")
            return
        if self.state.view_mode == "thread":
            title = f"{post.author}-thread"
            text = render_thread_for_writer(post)
        else:
            title = post.author
            text = render_post_for_writer(post)
        if hasattr(self.app, "open_in_writer_from_text"):
            self.app.open_in_writer_from_text(title, text)
        else:
            self.set_message("Writer handoff unavailable")

    def _sync_in_background(self) -> None:
        """Start a Mastodon sync in a worker thread with a spinner indicator."""
        if self._spinner_active:
            self.set_message("Sync already in progress…")
            return
        self._start_spinner()
        self.set_message("Syncing…")
        self._do_sync_worker()

    @work(thread=True, exclusive=True)
    def _do_sync_worker(self) -> None:
        """Worker: runs sync off the main thread, then posts result back."""
        message = self.state.sync_from_api()
        self.app.call_from_thread(self._on_sync_done, message)

    def _on_sync_done(self, message: str) -> None:
        """Called on the main thread after sync completes."""
        self._stop_spinner()
        self.set_message(message)
        self._refresh()
        self._persist_state()

    def _persist_state(self) -> None:
        """Persist account selection and cached posts to disk."""
        try:
            from safari_fed.app import persist_fed_state

            persist_fed_state(self.state)
        except Exception as exc:
            message = f"Could not save Safari Fed state: {exc}"
            self.set_message(message)
            self.notify(message, severity="error")

    def _quit_fed(self) -> None:
        self._persist_state()
        if hasattr(self.app, "quit_fed"):
            self.app.quit_fed()
        else:
            self.app.exit()

    def _refresh(self) -> None:
        self.state.ensure_selection()
        self.state.persist_active_account()
        self.query_one("#fed-title", Static).update(self._render_title())
        self.query_one("#fed-folders", Static).update(self._render_folders())
        self.query_one("#fed-accounts", Static).update(self._render_accounts())
        self.query_one("#fed-sidebar-title", Static).update(
            self._render_sidebar_title()
        )
        self.query_one("#fed-index", Static).update(self._render_index())
        self.query_one("#fed-detail-title", Static).update(self._render_detail_title())
        self.query_one("#fed-detail", Static).update(self._render_detail())
        self.query_one("#fed-command", Static).update(self._render_command_bar())
        self._refresh_status()

    def _refresh_status(self) -> None:
        self.query_one("#fed-status", Static).update(
            f"{self.state.status_message} | {self.state.last_sync_label}"
        )

    def _render_title(self) -> str:
        spinner = (
            f"{_SPINNER_FRAMES[self._spinner_frame]} " if self._spinner_active else " "
        )
        return (
            f"{spinner}SAFARI-FED  {self.state.current_folder}  "
            f"{self.state.unread_total()} unread  "
            f"{self.state.mention_total()} mentions  "
            f"acct={self.state.account_label}  "
            f"view={self.state.view_mode.upper()}"
        )

    def _render_folders(self) -> str:
        parts: list[str] = []
        for folder in FOLDER_ORDER:
            label = f"[{folder}]" if folder == self.state.current_folder else folder
            parts.append(f"{label}({self.state.folder_count(folder)})")
        return " Folders: " + "  ".join(parts) + "  Tab Cycle  U Sync  W Writer  O OPML"

    def _render_accounts(self) -> str:
        parts: list[str] = []
        for index, account_id in enumerate(self.state.account_ids(), start=1):
            label = f"{index}:{account_id}"
            if account_id == self.state.active_account_id:
                label = f"[{label}]"
            parts.append(label)
        return " Accounts: " + "  ".join(parts) + "  A Cycle  1-9 Select "

    def _render_sidebar_title(self) -> str:
        if self.state.view_mode == "compose":
            return " COMPOSE META "
        return f" {self.state.current_folder.upper()} INDEX "

    def _render_index(self) -> str:
        if self.state.view_mode == "compose":
            return self._render_compose_sidebar()
        posts = self.state.visible_posts()
        if not posts:
            return "No posts in this folder."
        # col layout: cursor(1) idx(2) sp flag(1) sp author(42) sp age(6) sp bst(3) sp fav(3) sp preview
        hdr_author = f"{'Author/Handle':<42}"
        lines = [
            f" # F {hdr_author} Age    Bst Fav Preview",
            "-" * 92,
        ]
        for index, post in enumerate(posts, start=1):
            author = self._clip(f"{post.author} {post.handle}", 42)
            preview = self._clip(post.preview_text, 26)
            line = (
                f" {index:>2} {self._flag(post):<1} {author:<42} "
                f"{post.age:<6} {post.boosts:>3} {post.favourites:>3} {preview}"
            )
            if index - 1 == self.state.selected_index:
                line = f"[reverse]{line}[/reverse]"
            lines.append(line)
        return "\n".join(lines)

    def _render_detail_title(self) -> str:
        post = self.state.current_post()
        if self.state.view_mode == "compose":
            return " COMPOSE POST "
        if self.state.view_mode == "thread" and post is not None:
            return f" THREAD VIEW  {post.thread_title} "
        if self.state.view_mode == "reader" and post is not None:
            return f" READER  {post.handle} "
        return " PREVIEW "

    def _render_detail(self) -> str:
        post = self.state.current_post()
        if self.state.view_mode == "compose":
            return self._render_compose_detail()
        if post is None:
            return "No post selected."
        if self.state.view_mode == "thread":
            return self._render_thread(post)
        if self.state.view_mode == "reader":
            return self._render_reader(post)
        return self._render_preview(post)

    def _render_preview(self, post: FedPost) -> str:
        lines = [
            f"Author: {post.handle}",
            f"Posted: {post.posted_at}",
            f"Visibility: {post.visibility}",
            f"Flags: {', '.join(post.flags) if post.flags else 'none'}",
            f"Tags: {' '.join(post.tags) if post.tags else '(none)'}",
            "-" * 86,
        ]
        lines.extend(self._wrap_block(post.content_lines, width=86, limit=16))
        if post.attachments:
            lines.append("")
            lines.extend(post.attachments)
        return "\n".join(lines)

    def _render_reader(self, post: FedPost) -> str:
        lines = [
            f"Post {self.state.selected_index + 1} of {len(self.state.visible_posts())}",
            f"Author:   {post.handle}",
            f"Posted:   {post.posted_at}",
            f"CW:       {post.cw}",
            f"Tags:     {' '.join(post.tags) if post.tags else 'none'}",
            "-" * 86,
        ]
        lines.extend(self._wrap_block(post.content_lines, width=86, limit=24))
        lines.extend(
            [
                "-" * 86,
                f"Replies: {post.replies}   Boosts: {post.boosts}   Favourites: {post.favourites}",
            ]
        )
        return "\n".join(lines)

    def _render_thread(self, post: FedPost) -> str:
        lines = [f"Thread: {post.thread_title}", "", *post.thread_lines]
        if post.attachments:
            lines.extend(["", *post.attachments])
        return "\n".join(lines)

    def _render_compose_sidebar(self) -> str:
        reply_target = self.state.current_post()
        replying_to = (
            reply_target.handle
            if self.state.reply_to_id is not None and reply_target is not None
            else "(new post)"
        )
        return "\n".join(
            [
                f"Folder:      {self.state.current_folder}",
                f"Visibility:  {self.state.compose_visibility}",
                f"CW:          {self.state.compose_cw}",
                f"Replying to: {replying_to}",
                "",
                "Ctrl+X Send",
                "Ctrl+S Save Draft",
                "Esc    Cancel",
                "W      Send to Writer",
            ]
        )

    def _render_compose_detail(self) -> str:
        body = self.state.compose_lines or [""]
        return "\n".join(
            [
                "Write calmly; sync later.",
                "-" * 58,
                *body,
                "-" * 58,
                "Ctrl+X Send  Ctrl+S Save Draft  Esc Cancel",
            ]
        )

    def _render_command_bar(self) -> str:
        if self.state.view_mode == "compose":
            return " Ctrl+X Send  Ctrl+S Save Draft  Esc Cancel  F1 Help "
        if self.state.view_mode == "thread":
            return " J/K Move  C Compose  R Reply  W Writer  O OPML  Esc Index  Tab Folder  F1 Help "
        if self.state.view_mode == "reader":
            return " J/K Prev/Next  T Thread  C Compose  R Reply  W Writer  O OPML  Esc Index  F1 Help "
        return " J/K Move  Enter View  C Compose  R Reply  B Boost  F Fav  W Writer  O OPML  F1 Help "

    def _flag(self, post: FedPost) -> str:
        if post.draft:
            return "D"
        if post.mention:
            return "@"
        if post.bookmarked:
            return "!"
        if post.direct:
            return "P"
        if post.unread:
            return "*"
        if post.sent:
            return "S"
        return " "

    def _clip(self, value: str, width: int) -> str:
        return shorten(value, width=width, placeholder="...")

    def _wrap_block(self, lines: list[str], width: int, limit: int) -> list[str]:
        rendered: list[str] = []
        for raw_line in lines:
            wrapped = wrap(raw_line, width=width) or [""]
            rendered.extend(wrapped)
            if len(rendered) >= limit:
                return rendered[:limit]
        return rendered[:limit]


# =====================================================================
# Safari Feed — RSS/Atom reader screens
# =====================================================================

_STATUS_BAR_STYLE = "bold reverse"
_FOOTER_STYLE = "reverse"
_FEED_SCREEN_CSS = """
SafariFeedMainScreen,
SafariFeedListScreen,
SafariFeedReaderScreen {
    align: center middle;
}

#feed-library-summary,
#feed-library-status,
#feed-list-status,
#feed-reader-status {
    height: 1;
}

#feed-opml-list,
#feed-list {
    height: 1fr;
}

#feed-reader-body {
    height: 1fr;
    layout: horizontal;
}

#feed-reader-index {
    width: 44;
    min-width: 32;
    height: 1fr;
    padding: 0 1;
}

#feed-reader-detail {
    width: 1fr;
    height: 1fr;
    padding: 0 1;
}
"""


class SafariFeedMainScreen(Screen[None]):
    """OPML library screen for Safari Feed (RSS reader)."""

    CSS = _FEED_SCREEN_CSS

    BINDINGS = [
        Binding("up", "cursor_up", "Up", show=False),
        Binding("down", "cursor_down", "Down", show=False),
        Binding("enter", "open_selected", "Open", show=False),
        Binding("r", "rescan", "Rescan", show=False),
        Binding("q", "go_back", "Back", show=False),
        Binding("escape", "go_back", "Back", show=False),
        Binding("h", "help_screen", "Help", show=False),
    ]

    def __init__(self, state: SafariFeedState) -> None:
        super().__init__()
        self.state = state
        self._selected_index = 0
        self._digit_buffer = ""
        self._digit_timer = None
        if not self.state.opml_documents:
            self.state.opml_documents = scan_opml_documents(self.state.config_dir)

    def compose(self) -> ComposeResult:
        config_dir = self.state.config_dir
        yield Static(
            f"[{_STATUS_BAR_STYLE}]  SAFARI FEED — OPML LIBRARY  [/{_STATUS_BAR_STYLE}]"
        )
        yield Static("", id="feed-library-summary")
        if not self.state.opml_documents:
            yield Static(
                f"  No OPML files found in {config_dir}\n"
                "  Drop one or more *.opml files there, then press R to rescan."
            )
        yield Static("", id="feed-opml-list")
        yield Static("", id="feed-library-status")
        yield Static(
            f"[{_FOOTER_STYLE}]  Up/Down=Move  Enter=Open  R=Rescan  Q=Back  H=Help  [/{_FOOTER_STYLE}]"
        )

    def on_mount(self) -> None:
        self._refresh_documents()

    def _refresh_documents(self) -> None:
        self.state.opml_documents = scan_opml_documents(self.state.config_dir)
        self.query_one("#feed-library-summary", Static).update(
            f"  Files: {len(self.state.opml_documents)}   Refreshed: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )
        self.query_one("#feed-library-status", Static).update(
            f"  {self.state.status_message}"
        )
        self._render_list()

    def _render_list(self) -> None:
        if not self.state.opml_documents:
            self.query_one("#feed-opml-list", Static).update("")
            return
        lines: list[str] = []
        for index, document in enumerate(self.state.opml_documents):
            line = (
                f"  {index + 1:>3}. {document.filename:<30}"
                f" {document.modified_label:<16} {document.feed_count:>4} feeds"
            )
            if index == self._selected_index:
                line = f"[reverse]{line}[/reverse]"
            lines.append(line)
        self.query_one("#feed-opml-list", Static).update("\n".join(lines))

    def _clamp_index(self) -> None:
        count = len(self.state.opml_documents)
        if count == 0:
            self._selected_index = 0
        else:
            self._selected_index = max(0, min(self._selected_index, count - 1))

    def _selected_document(self):
        if 0 <= self._selected_index < len(self.state.opml_documents):
            return self.state.opml_documents[self._selected_index]
        return None

    def action_cursor_up(self) -> None:
        if self._selected_index > 0:
            self._selected_index -= 1
            self._render_list()

    def action_cursor_down(self) -> None:
        if self._selected_index < len(self.state.opml_documents) - 1:
            self._selected_index += 1
            self._render_list()

    def _commit_digit_selection(self) -> None:
        """Apply accumulated digit buffer as a selection jump."""
        if not self._digit_buffer:
            return
        index = int(self._digit_buffer) - 1
        self._digit_buffer = ""
        self._digit_timer = None
        if 0 <= index < len(self.state.opml_documents):
            self._selected_index = index
            self._render_list()

    def on_key(self, event: Key) -> None:
        if not event.character or not event.character.isdigit():
            if self._digit_buffer:
                self._digit_buffer = ""
                if self._digit_timer is not None:
                    self._digit_timer.stop()
                    self._digit_timer = None
            return
        if event.character == "0" and not self._digit_buffer:
            return
        candidate = f"{self._digit_buffer}{event.character}"
        value = int(candidate)
        has_exact = 1 <= value <= len(self.state.opml_documents)
        has_longer_prefix = any(
            str(number).startswith(candidate)
            for number in range(1, len(self.state.opml_documents) + 1)
            if len(str(number)) > len(candidate)
        )
        if not has_exact and not has_longer_prefix:
            self._digit_buffer = ""
            return
        self._digit_buffer = candidate
        event.stop()
        event.prevent_default()
        if self._digit_timer is not None:
            self._digit_timer.stop()
        if has_exact:
            self._selected_index = value - 1
            self._render_list()
        if has_exact and not has_longer_prefix:
            self._digit_buffer = ""
            self._digit_timer = None
            return
        self._digit_timer = self.set_timer(0.8, self._commit_digit_selection)

    def action_open_selected(self) -> None:
        document = self._selected_document()
        if document is None:
            return
        self.state.current_opml = document
        text = document.path.read_text(encoding="utf-8", errors="replace")
        self.state.feeds = parse_opml_document(text)
        self.state.current_feed_index = 0
        self.state.current_item_index = 0
        self.app.push_screen(SafariFeedListScreen(self.state))

    def action_rescan(self) -> None:
        self.state.status_message = "OPML library rescanned"
        self._refresh_documents()
        self.app.pop_screen()
        self.app.push_screen(SafariFeedMainScreen(self.state))

    def action_help_screen(self) -> None:
        self.notify("Safari Feed: browse OPML, fetch feeds, read calmly.")

    def action_go_back(self) -> None:
        if hasattr(self.app, "quit_feed"):
            self.app.quit_feed()
        elif hasattr(self.app, "quit_fed"):
            self.app.quit_fed()
        else:
            self.app.pop_screen()


class SafariFeedListScreen(Screen[None]):
    """Feed list inside a selected OPML document."""

    CSS = _FEED_SCREEN_CSS

    BINDINGS = [
        Binding("up", "cursor_up", "Up", show=False),
        Binding("down", "cursor_down", "Down", show=False),
        Binding("enter", "open_feed", "Open Feed", show=False),
        Binding("f", "fetch_current", "Fetch", show=False),
        Binding("a", "fetch_all", "Fetch All", show=False),
        Binding("r", "refresh_list", "Refresh List", show=False),
        Binding("q", "go_back", "Back", show=False),
        Binding("escape", "go_back", "Back", show=False),
    ]

    def __init__(self, state: SafariFeedState) -> None:
        super().__init__()
        self.state = state
        self._selected_index = state.current_feed_index
        self._digit_buffer = ""
        self._digit_timer = None

    def compose(self) -> ComposeResult:
        title = self.state.current_opml.filename if self.state.current_opml else "OPML"
        yield Static(f"[{_STATUS_BAR_STYLE}]  FEEDS — {title}  [/{_STATUS_BAR_STYLE}]")
        if not self.state.feeds:
            yield Static("  No feeds in this OPML file.")
        yield Static("", id="feed-list")
        yield Static(f"  {self.state.status_message}", id="feed-list-status")
        yield Static(
            f"[{_FOOTER_STYLE}]  Up/Down=Move  Enter=Open Feed  F=Fetch  A=Fetch All  R=Refresh List  Q=Back  [/{_FOOTER_STYLE}]"
        )

    def on_mount(self) -> None:
        self._clamp_index()
        self._render_list()

    def _clamp_index(self) -> None:
        count = len(self.state.feeds)
        if count == 0:
            self._selected_index = 0
        else:
            self._selected_index = max(0, min(self._selected_index, count - 1))

    def _render_list(self) -> None:
        if not self.state.feeds:
            self.query_one("#feed-list", Static).update("")
            return
        lines: list[str] = []
        for index, feed in enumerate(self.state.feeds):
            line = (
                f"  {index + 1:>3}. {feed.group[:16]:<16} {feed.title[:28]:<28}"
                f" {feed.domain[:18]:<18} {feed.unread_count:>4} unread  {feed.last_fetched or 'never':<16}"
            )
            if index == self._selected_index:
                line = f"[reverse]{line}[/reverse]"
            lines.append(line)
        self.query_one("#feed-list", Static).update("\n".join(lines))

    def action_cursor_up(self) -> None:
        if self._selected_index > 0:
            self._selected_index -= 1
            self._render_list()

    def action_cursor_down(self) -> None:
        if self._selected_index < len(self.state.feeds) - 1:
            self._selected_index += 1
            self._render_list()

    def _commit_digit_selection(self) -> None:
        """Apply accumulated digit buffer as a selection jump."""
        if not self._digit_buffer:
            return
        index = int(self._digit_buffer) - 1
        self._digit_buffer = ""
        self._digit_timer = None
        if 0 <= index < len(self.state.feeds):
            self._selected_index = index
            self._render_list()

    def on_key(self, event: Key) -> None:
        if not event.character or not event.character.isdigit():
            if self._digit_buffer:
                self._digit_buffer = ""
                if self._digit_timer is not None:
                    self._digit_timer.stop()
                    self._digit_timer = None
            return
        if event.character == "0" and not self._digit_buffer:
            return
        candidate = f"{self._digit_buffer}{event.character}"
        value = int(candidate)
        has_exact = 1 <= value <= len(self.state.feeds)
        has_longer_prefix = any(
            str(number).startswith(candidate)
            for number in range(1, len(self.state.feeds) + 1)
            if len(str(number)) > len(candidate)
        )
        if not has_exact and not has_longer_prefix:
            self._digit_buffer = ""
            return
        self._digit_buffer = candidate
        event.stop()
        event.prevent_default()
        if self._digit_timer is not None:
            self._digit_timer.stop()
        if has_exact:
            self._selected_index = value - 1
            self._render_list()
        if has_exact and not has_longer_prefix:
            self._digit_buffer = ""
            self._digit_timer = None
            return
        self._digit_timer = self.set_timer(0.8, self._commit_digit_selection)

    def _selected_feed(self) -> FeedRecord | None:
        if 0 <= self._selected_index < len(self.state.feeds):
            self.state.current_feed_index = self._selected_index
            return self.state.feeds[self._selected_index]
        return None

    def action_open_feed(self) -> None:
        feed = self._selected_feed()
        if feed is None:
            return
        self.state.current_item_index = 0
        try:
            fetch_feed(feed)
            _apply_read_state(self.state, feed)
            self.state.status_message = f"Fetched {feed.title}"
        except Exception:
            feed.fetch_status = "ERROR"
            self.state.status_message = "FEED FETCH FAILED"
        self.app.push_screen(SafariFeedReaderScreen(self.state))

    def action_fetch_current(self) -> None:
        feed = self._selected_feed()
        if feed is None:
            return
        try:
            fetch_feed(feed)
            _apply_read_state(self.state, feed)
            self.state.status_message = f"Fetched {feed.title}"
        except Exception:
            feed.fetch_status = "ERROR"
            self.state.status_message = "FEED FETCH FAILED"
        self.app.pop_screen()
        self.app.push_screen(SafariFeedListScreen(self.state))

    def action_fetch_all(self) -> None:
        fetched = 0
        for feed in self.state.feeds:
            try:
                fetch_feed(feed)
                _apply_read_state(self.state, feed)
                fetched += 1
            except Exception:
                feed.fetch_status = "ERROR"
        self.state.status_message = f"Fetched {fetched} feed(s)"
        self.app.pop_screen()
        self.app.push_screen(SafariFeedListScreen(self.state))

    def action_refresh_list(self) -> None:
        self.state.status_message = "Feed list refreshed"
        self.app.pop_screen()
        self.app.push_screen(SafariFeedListScreen(self.state))

    def action_go_back(self) -> None:
        self.app.pop_screen()


class SafariFeedReaderScreen(Screen[None]):
    """Split-pane reader for one fetched feed."""

    CSS = _FEED_SCREEN_CSS

    BINDINGS = [
        Binding("up", "move_up", "Up", show=False),
        Binding("down", "move_down", "Down", show=False),
        Binding("enter", "read_item", "Read", show=False),
        Binding("m", "toggle_read", "Mark", show=False),
        Binding("f", "fetch_feed_again", "Fetch Feed", show=False),
        Binding("o", "fetch_article", "Fetch Article", show=False),
        Binding("t", "toggle_source", "Toggle Source", show=False),
        Binding("v", "toggle_render", "Toggle Render", show=False),
        Binding("n", "next_unread", "Next Unread", show=False),
        Binding("p", "previous_unread", "Prev Unread", show=False),
        Binding("q", "go_back", "Back", show=False),
        Binding("escape", "go_back", "Back", show=False),
    ]

    def __init__(self, state: SafariFeedState) -> None:
        super().__init__()
        self.state = state

    def compose(self) -> ComposeResult:
        yield Static("", id="feed-reader-header")
        with Horizontal(id="feed-reader-body"):
            yield Static("", id="feed-reader-index")
            yield Static("", id="feed-reader-detail")
        yield Static("", id="feed-reader-status")
        yield Static(
            f"[{_FOOTER_STYLE}]  Up/Down=Move  Enter=Read  M=Mark  F=Fetch Feed  O=Fetch Article  T=Feed/Fetched  V=Markdown/ANSI  Q=Back  [/{_FOOTER_STYLE}]"
        )

    def on_mount(self) -> None:
        self._refresh()

    def _refresh(self) -> None:
        self.state.ensure_indexes()
        feed = self.state.current_feed()
        item = self.state.current_item()
        if feed is None:
            self.query_one("#feed-reader-header", Static).update(
                f"[{_STATUS_BAR_STYLE}]  SAFARI FEED — EMPTY  [/{_STATUS_BAR_STYLE}]"
            )
            self.query_one("#feed-reader-index", Static).update("No feed selected.")
            self.query_one("#feed-reader-detail", Static).update("")
            self.query_one("#feed-reader-status", Static).update("READY")
            return
        position = self.state.current_item_index + 1 if item is not None else 0
        total = len(feed.items)
        self.query_one("#feed-reader-header", Static).update(
            f"[{_STATUS_BAR_STYLE}]  {feed.title}  {position}/{total}  "
            f"{self.state.content_source}  {self.state.render_mode}  "
            f"{feed.fetch_status or 'NEVER'}  [/{_STATUS_BAR_STYLE}]"
        )
        self.query_one("#feed-reader-index", Static).update(self._render_index(feed))
        self.query_one("#feed-reader-detail", Static).update(self._render_detail(item))
        self.query_one("#feed-reader-status", Static).update(
            f"  {self.state.status_message}"
        )

    def _render_index(self, feed: FeedRecord) -> str:
        if not feed.items:
            return "No items. Press F to fetch this feed."
        lines = [" # U Published           Title", "-" * 60]
        for index, item in enumerate(feed.items, start=1):
            unread = "*" if item.unread else " "
            published = (item.published or "")[:18]
            title = item.title[:34]
            line = f" {index:>2} {unread} {published:<18} {title}"
            if index - 1 == self.state.current_item_index:
                line = f"[reverse]{line}[/reverse]"
            lines.append(line)
        return "\n".join(lines)

    def _render_detail(self, item) -> str:
        if item is None:
            return "No article selected."
        body = render_entry_source(
            item,
            self.state.content_source,
            self.state.render_mode,
        )
        return "\n".join(
            [
                f"Title: {item.title}",
                f"Author: {item.author or '(unknown)'}",
                f"Published: {item.published or '(unknown)'}",
                f"URL: {item.link or '(none)'}",
                "-" * 72,
                body,
            ]
        )

    def action_move_up(self) -> None:
        self.state.current_item_index = max(0, self.state.current_item_index - 1)
        self._refresh()

    def action_move_down(self) -> None:
        feed = self.state.current_feed()
        if feed is None:
            return
        self.state.current_item_index = min(
            len(feed.items) - 1,
            self.state.current_item_index + 1,
        )
        self._refresh()

    def action_read_item(self) -> None:
        item = self.state.current_item()
        if item is None:
            return
        item.unread = False
        self.state.status_message = f"Reading {item.title}"
        _save_item_state(self.state)
        self._refresh()

    def action_toggle_read(self) -> None:
        item = self.state.current_item()
        if item is None:
            return
        item.unread = not item.unread
        self.state.status_message = "Marked unread" if item.unread else "Marked read"
        _save_item_state(self.state)
        self._refresh()

    def action_fetch_feed_again(self) -> None:
        feed = self.state.current_feed()
        if feed is None:
            return
        try:
            fetch_feed(feed)
            _apply_read_state(self.state, feed)
            self.state.status_message = f"Fetched {feed.title}"
        except Exception:
            feed.fetch_status = "ERROR"
            self.state.status_message = "FEED FETCH FAILED"
        self._refresh()

    def action_fetch_article(self) -> None:
        item = self.state.current_item()
        if item is None:
            return
        try:
            article = fetch_article(item)
            self.state.content_source = "FETCHED"
            self.state.status_message = (
                "Article fetched"
                if article.status == "ONLINE"
                else "Fetched article loaded from cache"
            )
        except Exception:
            self.state.status_message = "ARTICLE FETCH FAILED"
        self._refresh()

    def action_toggle_source(self) -> None:
        item = self.state.current_item()
        if item is None:
            return
        if self.state.content_source == "FEED":
            if item.article is None:
                try:
                    fetch_article(item)
                except Exception:
                    self.state.status_message = "ARTICLE FETCH FAILED"
                    self._refresh()
                    return
            self.state.content_source = "FETCHED"
        else:
            self.state.content_source = "FEED"
        self.state.status_message = f"Source: {self.state.content_source}"
        _save_item_state(self.state)
        self._refresh()

    def action_toggle_render(self) -> None:
        self.state.render_mode = "ANSI" if self.state.render_mode == "MD" else "MD"
        self.state.status_message = f"Render: {self.state.render_mode}"
        _save_item_state(self.state)
        self._refresh()

    def action_next_unread(self) -> None:
        feed = self.state.current_feed()
        if feed is None:
            return
        for index in range(self.state.current_item_index + 1, len(feed.items)):
            if feed.items[index].unread:
                self.state.current_item_index = index
                self.state.status_message = "Jumped to next unread item"
                self._refresh()
                return
        self.state.status_message = "No next unread item"
        self._refresh()

    def action_previous_unread(self) -> None:
        feed = self.state.current_feed()
        if feed is None:
            return
        for index in range(self.state.current_item_index - 1, -1, -1):
            if feed.items[index].unread:
                self.state.current_item_index = index
                self.state.status_message = "Jumped to previous unread item"
                self._refresh()
                return
        self.state.status_message = "No previous unread item"
        self._refresh()

    def action_go_back(self) -> None:
        self.app.pop_screen()


def _apply_read_state(state: SafariFeedState, feed: FeedRecord) -> None:
    saved = load_feed_preferences()
    read_items = saved.get("read_items", {})
    for item in feed.items:
        item.unread = not bool(read_items.get(item.item_id))
    feed.unread_count = sum(1 for item in feed.items if item.unread)
    state.render_mode = saved.get("render_mode", state.render_mode)
    state.content_source = saved.get("content_source", state.content_source)


def _save_item_state(state: SafariFeedState) -> None:
    payload = load_feed_preferences()
    read_items = payload.setdefault("read_items", {})
    for feed in state.feeds:
        for item in feed.items:
            if not item.unread:
                read_items[item.item_id] = True
            elif item.item_id in read_items:
                del read_items[item.item_id]
        feed.unread_count = sum(1 for item in feed.items if item.unread)
    payload["render_mode"] = state.render_mode
    payload["content_source"] = state.content_source
    save_feed_preferences(payload)
