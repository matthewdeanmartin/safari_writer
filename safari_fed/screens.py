"""Textual screens for Safari Fed."""

from __future__ import annotations

from textwrap import shorten, wrap

from textual import events, work
from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.screen import ModalScreen, Screen
from textual.timer import Timer
from textual.widgets import Static

from safari_fed.state import (
    FOLDER_ORDER,
    FedPost,
    SafariFedState,
    render_post_for_writer,
    render_thread_for_writer,
)

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
  W                 Export to Writer      ~                 Run macro → Draft

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
        return " Folders: " + "  ".join(parts) + "  Tab Cycle  U Sync  W Writer"

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
            return " J/K Move  C Compose  R Reply  W Writer  Esc Index  Tab Folder  F1 Help "
        if self.state.view_mode == "reader":
            return " J/K Prev/Next  T Thread  C Compose  R Reply  W Writer  Esc Index  F1 Help "
        return " J/K Move  Enter View  C Compose  R Reply  B Boost  F Fav  W Writer  F1 Help "

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
