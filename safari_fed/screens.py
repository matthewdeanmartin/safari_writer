"""Textual screens for Safari Fed."""

from __future__ import annotations

from textwrap import shorten, wrap

from textual import events, work
from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.screen import ModalScreen, Screen
from textual.timer import Timer
from textual.widgets import Static

from safari_fed.opml import (DEFAULT_MAX_ACCOUNTS, DEFAULT_MAX_FEEDS,
                             default_opml_export_path,
                             export_followed_feeds_to_opml)
from safari_fed.state import (FOLDER_ORDER, FedPost, SafariFedState,
                              render_post_for_writer, render_thread_for_writer)

__all__ = ["FED_CSS", "FedHelpScreen", "SafariFedMainScreen"]

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
    width: 64;
    height: 10;
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

    def _prompt_for_opml_export(self) -> None:
        """Ask for bounded OPML export limits before starting."""
        if self._spinner_active:
            self.set_message("Another network task is already in progress…")
            return
        self.app.push_screen(FedOpmlLimitsScreen(), self._on_opml_limits_selected)

    def _on_opml_limits_selected(
        self,
        result: tuple[int, int] | None,
    ) -> None:
        """Start OPML export if the user confirmed limits."""
        if result is None:
            self.set_message("OPML export cancelled")
            self._refresh()
            return
        max_accounts, max_feeds = result
        self._export_opml_in_background(max_accounts=max_accounts, max_feeds=max_feeds)

    def _export_opml_in_background(
        self,
        *,
        max_accounts: int,
        max_feeds: int,
    ) -> None:
        """Start followed-feed OPML export in a worker thread."""
        if self._spinner_active:
            self.set_message("Another network task is already in progress…")
            return
        if self.state.client is None:
            self.set_message("No Mastodon credentials found; cannot export OPML")
            self._refresh()
            return
        self._start_spinner()
        self.set_message(
            f"Scavenging feeds from up to {max_accounts} accounts for {max_feeds} feeds…"
        )
        self._do_export_opml_worker(max_accounts, max_feeds)

    @work(thread=True, exclusive=True)
    def _do_export_opml_worker(self, max_accounts: int, max_feeds: int) -> None:
        """Worker: discover followed feeds and write the OPML file."""
        try:
            account_name = self.state.active_account_id or None
            output_path = default_opml_export_path(account_name)
            subscriptions = export_followed_feeds_to_opml(
                self.state.client,
                output_path,
                max_accounts=max_accounts,
                max_feeds=max_feeds,
            )
            message = f"Exported {len(subscriptions)} feeds to {output_path}"
        except Exception as error:
            message = f"OPML export error: {error}"
        self.app.call_from_thread(self._on_export_opml_done, message)

    def _on_export_opml_done(self, message: str) -> None:
        """Called on the main thread after OPML export completes."""
        self._stop_spinner()
        self.set_message(message)
        self._refresh()

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
            cursor = ">" if index - 1 == self.state.selected_index else " "
            author = self._clip(f"{post.author} {post.handle}", 42)
            preview = self._clip(post.preview_text, 26)
            lines.append(
                f"{cursor}{index:>2} {self._flag(post):<1} {author:<42} "
                f"{post.age:<6} {post.boosts:>3} {post.favourites:>3} {preview}"
            )
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
