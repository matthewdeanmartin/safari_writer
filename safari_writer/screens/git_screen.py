"""Git Publish screen — commit and push blog posts without leaving Safari Writer."""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator, Optional, Protocol, Sequence, cast

from textual import events
from textual.app import ComposeResult
from textual.containers import Container
from textual.screen import ModalScreen, Screen
from textual.widgets import Static

# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------

GIT_CSS = """
GitPublishScreen {
    background: $background;
    color: $foreground;
}

#git-header {
    dock: top;
    height: 1;
    background: $primary;
    color: $text;
    padding: 0 1;
}

#git-footer {
    dock: bottom;
    height: 2;
    background: $primary;
    color: $text;
    padding: 0 1;
}

#git-main {
    height: 1fr;
    layout: horizontal;
}

#git-menu-pane {
    width: 30;
    min-width: 30;
    height: 100%;
    border: solid $accent;
    background: $surface;
    padding: 1;
    margin-right: 1;
}

#git-menu-title {
    color: $accent;
    text-style: bold;
    text-align: center;
    margin-bottom: 1;
}

#git-menu-items {
    color: $foreground;
}

#git-content {
    width: 1fr;
    height: 100%;
    layout: horizontal;
}

#git-status-pane {
    width: 1fr;
    height: 100%;
    border: solid $accent;
    background: $surface;
    padding: 1;
    margin-right: 1;
}

#git-status-title {
    color: $accent;
    text-style: bold;
    text-align: center;
    margin-bottom: 1;
}

#git-status-body {
    height: 1fr;
    color: $foreground;
}

#git-history-pane {
    width: 40%;
    height: 100%;
    border: solid $accent;
    background: $surface;
    padding: 1;
}

#git-history-title {
    color: $accent;
    text-style: bold;
    text-align: center;
    margin-bottom: 1;
}

#git-history-body {
    height: 1fr;
    color: $foreground;
}

GitHelpScreen {
    align: center middle;
}

#git-help-dialog {
    width: 72;
    height: auto;
    max-height: 90%;
    border: solid $primary;
    background: $surface;
    padding: 1 2;
}

#git-help-title {
    text-align: center;
    text-style: bold;
    color: $accent;
    margin-bottom: 1;
}

#git-help-content {
    color: $foreground;
}

#git-help-footer {
    text-align: center;
    color: $text-muted;
    margin-top: 1;
}

GitMessageScreen {
    align: center middle;
    background: $background 60%;
}

#git-msg-dialog {
    width: 72;
    height: auto;
    border: solid $accent;
    background: $surface;
    padding: 1 2;
}

#git-msg-title {
    color: $accent;
    text-style: bold;
    text-align: center;
}

#git-msg-body {
    margin-top: 1;
    color: $foreground;
}

#git-msg-input {
    margin-top: 1;
    color: $foreground;
}

#git-msg-hint {
    color: $text-muted;
    margin-top: 1;
}
"""

HELP_TEXT = """\
[bold]*** SAFARI WRITER — GIT PUBLISH HELP ***[/bold]

[bold underline]S[/bold underline]  Status      Show working tree status (modified / untracked files)
[bold underline]A[/bold underline]  Add All     Stage all changes in the current directory
[bold underline]C[/bold underline]  Commit      Enter a commit message and commit staged changes
[bold underline]P[/bold underline]  Push        Push commits to the remote (origin/current branch)
[bold underline]U[/bold underline]  Pull        Pull latest commits from remote
[bold underline]H[/bold underline]  History     Refresh the git log shown on the right pane
[bold underline]R[/bold underline]  Repo Path   Change the repository directory
[bold underline]F1[/bold underline] Help        Show this help screen
[bold underline]Esc[/bold underline] Return     Go back to the previous screen

Quick workflow for a blogger:
  1. Write your post and Save it.
  2. Press G from the Print menu to open Git Publish.
  3. Press A to stage all changes.
  4. Press C and type a short commit message.
  5. Press P to push — your post is live!
"""

MENU_TEXT = """\
[bold underline]S[/]  Status
[bold underline]A[/]  Add All
[bold underline]C[/]  Commit
[bold underline]P[/]  Push
[bold underline]U[/]  Pull
[bold underline]H[/]  History
[bold underline]R[/]  Repo Path
[bold underline]F1[/] Help
[bold underline]Esc[/] Return
"""


# ---------------------------------------------------------------------------
# Helpers — thin wrappers around GitPython
# ---------------------------------------------------------------------------


def _find_repo_root(start: Path) -> Optional[Path]:
    """Walk up from *start* to find a .git directory; return its root or None."""
    current = start.resolve()
    for parent in [current, *current.parents]:
        if (parent / ".git").exists():
            return parent
    return None


@contextmanager
def _open_repo(repo_path: Path) -> Iterator[Any]:
    """Open a GitPython repo and ensure Windows subprocess resources are released."""
    import git

    repo = git.Repo(repo_path)
    try:
        yield repo
    finally:
        close = getattr(repo, "close", None)
        if callable(close):
            close()


def _git_status(repo_path: Path) -> str:
    """Return a human-readable status summary."""
    try:
        with _open_repo(repo_path) as repo:
            lines: list[str] = []
            lines.append(f"Branch: [bold]{repo.active_branch.name}[/bold]")
            lines.append(f"Remote: {_remote_url(repo)}")
            lines.append("")
            staged = repo.index.diff("HEAD") if repo.head.is_valid() else []
            unstaged = repo.index.diff(None)
            untracked = repo.untracked_files
            if staged:
                lines.append("[bold]Staged:[/bold]")
                for diff in staged:
                    lines.append(f"  [green]M  {diff.a_path}[/green]")
            if unstaged:
                lines.append("[bold]Modified (not staged):[/bold]")
                for diff in unstaged:
                    lines.append(f"  [yellow]M  {diff.a_path}[/yellow]")
            if untracked:
                lines.append("[bold]Untracked:[/bold]")
                for f in untracked[:20]:
                    lines.append(f"  [red]?  {f}[/red]")
            if not staged and not unstaged and not untracked:
                lines.append("[green]Working tree clean.[/green]")
            return "\n".join(lines)
    except Exception as exc:
        return f"[red]Error: {exc}[/red]"


class _GitRemoteLike(Protocol):
    url: str


def _remote_url(repo: Any) -> str:
    try:
        remotes = cast(Sequence[_GitRemoteLike], repo.remotes)
        if remotes:
            return remotes[0].url
        return "(no remote)"
    except Exception:
        return "(unknown)"


def _git_add_all(repo_path: Path) -> str:
    try:
        with _open_repo(repo_path) as repo:
            repo.git.add(A=True)
        return "[green]All changes staged.[/green]"
    except Exception as exc:
        return f"[red]Add failed: {exc}[/red]"


def _git_commit(repo_path: Path, message: str) -> str:
    try:
        with _open_repo(repo_path) as repo:
            if not message.strip():
                return "[yellow]Commit cancelled — empty message.[/yellow]"
            repo.index.commit(message.strip())
        return f"[green]Committed: {message.strip()!r}[/green]"
    except Exception as exc:
        return f"[red]Commit failed: {exc}[/red]"


def _git_push(repo_path: Path) -> str:
    try:
        with _open_repo(repo_path) as repo:
            if not repo.remotes:
                return "[yellow]No remote configured.[/yellow]"
            origin = repo.remotes[0]
            push_info = origin.push()
            if push_info:
                flags = push_info[0].flags
                # PushInfo.ERROR = 1024
                if flags & 1024:
                    return f"[red]Push error: {push_info[0].summary}[/red]"
            return f"[green]Pushed to {origin.name}.[/green]"
    except Exception as exc:
        return f"[red]Push failed: {exc}[/red]"


def _git_pull(repo_path: Path) -> str:
    try:
        with _open_repo(repo_path) as repo:
            if not repo.remotes:
                return "[yellow]No remote configured.[/yellow]"
            origin = repo.remotes[0]
            origin.pull()
            return f"[green]Pulled from {origin.name}.[/green]"
    except Exception as exc:
        return f"[red]Pull failed: {exc}[/red]"


def _git_log(repo_path: Path, count: int = 20) -> str:
    try:
        with _open_repo(repo_path) as repo:
            if not repo.head.is_valid():
                return "(no commits yet)"
            lines: list[str] = []
            for commit in list(repo.iter_commits(max_count=count)):
                sha = commit.hexsha[:7]
                raw_message = commit.message
                message = (
                    raw_message.decode("utf-8", errors="replace")
                    if isinstance(raw_message, bytes)
                    else raw_message
                )
                msg = message.split("\n")[0][:50]
                date = commit.committed_datetime.strftime("%m/%d %H:%M")
                lines.append(f"[dim]{sha}[/dim] [cyan]{date}[/cyan]\n  {msg}")
            return "\n".join(lines) if lines else "(no commits)"
    except Exception as exc:
        return f"[red]Log error: {exc}[/red]"


# ---------------------------------------------------------------------------
# Help modal
# ---------------------------------------------------------------------------


class GitHelpScreen(ModalScreen):
    CSS = GIT_CSS

    def compose(self) -> ComposeResult:
        with Container(id="git-help-dialog"):
            yield Static("*** GIT PUBLISH HELP ***", id="git-help-title")
            yield Static(HELP_TEXT, id="git-help-content")
            yield Static("Press any key to close", id="git-help-footer")

    def on_key(self, event: events.Key) -> None:
        self.dismiss()
        event.stop()


# ---------------------------------------------------------------------------
# Commit message input modal
# ---------------------------------------------------------------------------


class GitCommitInputScreen(ModalScreen[str | None]):
    CSS = GIT_CSS

    def __init__(self, default_msg: str = "") -> None:
        super().__init__()
        self._buf = default_msg

    def compose(self) -> ComposeResult:
        with Container(id="git-msg-dialog"):
            yield Static("*** COMMIT MESSAGE ***", id="git-msg-title")
            yield Static(
                "Enter a short description of your changes:", id="git-msg-body"
            )
            yield Static(self._render_input(), id="git-msg-input")
            yield Static("Enter=Commit  Esc=Cancel", id="git-msg-hint")

    def _render_input(self) -> str:
        return f"> {self._buf}[reverse] [/reverse]"

    def _refresh(self) -> None:
        self.query_one("#git-msg-input", Static).update(self._render_input())

    def on_key(self, event: events.Key) -> None:
        if event.key == "escape":
            self.dismiss(None)
        elif event.key == "enter":
            msg = self._buf.strip()
            self.dismiss(msg if msg else None)
        elif event.key == "backspace":
            self._buf = self._buf[:-1]
            self._refresh()
        elif event.character and event.character.isprintable():
            self._buf += event.character
            self._refresh()
        event.stop()


# ---------------------------------------------------------------------------
# Repo path input modal
# ---------------------------------------------------------------------------


class GitRepoPathScreen(ModalScreen[str | None]):
    CSS = GIT_CSS

    def __init__(self, current: str = "") -> None:
        super().__init__()
        self._buf = current

    def compose(self) -> ComposeResult:
        with Container(id="git-msg-dialog"):
            yield Static("*** REPOSITORY PATH ***", id="git-msg-title")
            yield Static(
                "Enter path to git repository (leave blank for auto-detect):",
                id="git-msg-body",
            )
            yield Static(self._render_input(), id="git-msg-input")
            yield Static("Enter=Set  Esc=Cancel", id="git-msg-hint")

    def _render_input(self) -> str:
        return f"> {self._buf}[reverse] [/reverse]"

    def _refresh(self) -> None:
        self.query_one("#git-msg-input", Static).update(self._render_input())

    def on_key(self, event: events.Key) -> None:
        if event.key == "escape":
            self.dismiss(None)
        elif event.key == "enter":
            val = self._buf.strip()
            self.dismiss(val if val else None)
        elif event.key == "backspace":
            self._buf = self._buf[:-1]
            self._refresh()
        elif event.character and event.character.isprintable():
            self._buf += event.character
            self._refresh()
        event.stop()


# ---------------------------------------------------------------------------
# Main Git Publish Screen
# ---------------------------------------------------------------------------


class GitPublishScreen(Screen):
    """Two-pane git publish screen for bloggers."""

    CSS = GIT_CSS

    def __init__(self, document_path: str = "") -> None:
        super().__init__()
        self._document_path = document_path
        self._repo_path: Optional[Path] = self._auto_detect_repo(document_path)
        self._status_text = ""
        self._history_text = ""

    # ------------------------------------------------------------------
    # Repo detection
    # ------------------------------------------------------------------

    def _auto_detect_repo(self, doc_path: str) -> Optional[Path]:
        """Find repo root from document path, then cwd."""
        if doc_path:
            found = _find_repo_root(Path(doc_path).parent)
            if found:
                return found
        return _find_repo_root(Path.cwd())

    def _repo_label(self) -> str:
        if self._repo_path:
            return str(self._repo_path)
        return "(no repository found)"

    # ------------------------------------------------------------------
    # Textual compose / mount
    # ------------------------------------------------------------------

    def compose(self) -> ComposeResult:
        yield Static("*** GIT PUBLISH ***", id="git-header")
        with Container(id="git-main"):
            with Container(id="git-menu-pane"):
                yield Static("ACTIONS", id="git-menu-title")
                yield Static(MENU_TEXT, id="git-menu-items")
            with Container(id="git-content"):
                with Container(id="git-status-pane"):
                    yield Static("STATUS", id="git-status-title")
                    yield Static("", id="git-status-body")
                with Container(id="git-history-pane"):
                    yield Static("RECENT COMMITS", id="git-history-title")
                    yield Static("", id="git-history-body")
        yield Static("", id="git-footer")

    def on_mount(self) -> None:
        self._refresh_all()

    # ------------------------------------------------------------------
    # Display helpers
    # ------------------------------------------------------------------

    def _refresh_all(self) -> None:
        self._refresh_status()
        self._refresh_history()
        self._update_footer("")

    def _refresh_status(self) -> None:
        if not self._repo_path:
            text = "[yellow]No git repository found.\nPress R to set path.[/yellow]"
        else:
            text = f"Repo: [bold]{self._repo_path}[/bold]\n\n"
            text += _git_status(self._repo_path)
        self.query_one("#git-status-body", Static).update(text)

    def _refresh_history(self) -> None:
        if not self._repo_path:
            text = "(no repository)"
        else:
            text = _git_log(self._repo_path)
        self.query_one("#git-history-body", Static).update(text)

    def _update_footer(self, msg: str) -> None:
        repo_label = self._repo_label()
        line1 = f" Repo: {repo_label}"
        line2 = (
            f" {msg}"
            if msg
            else " S=Status  A=AddAll  C=Commit  P=Push  U=Pull  F1=Help  Esc=Return"
        )
        self.query_one("#git-footer", Static).update(f"{line1}\n{line2}")

    def _set_status_msg(self, msg: str) -> None:
        """Show a result message in the status pane and refresh afterward."""
        current = self.query_one("#git-status-body", Static)
        current.update(msg)
        self._update_footer(
            msg.replace("[green]", "")
            .replace("[/green]", "")
            .replace("[red]", "")
            .replace("[/red]", "")
            .replace("[yellow]", "")
            .replace("[/yellow]", "")
        )

    # ------------------------------------------------------------------
    # Key handling
    # ------------------------------------------------------------------

    def on_key(self, event: events.Key) -> None:
        key = event.key.lower()

        if key == "escape":
            self.app.pop_screen()
        elif key == "f1":
            self.app.push_screen(GitHelpScreen())
        elif key == "s":
            self._refresh_status()
            self._update_footer("Status refreshed.")
        elif key == "a":
            self._action_add_all()
        elif key == "c":
            self._action_commit()
        elif key == "p":
            self._action_push()
        elif key == "u":
            self._action_pull()
        elif key == "h":
            self._refresh_history()
            self._update_footer("History refreshed.")
        elif key == "r":
            self._action_set_repo()

        event.stop()

    # ------------------------------------------------------------------
    # Git actions
    # ------------------------------------------------------------------

    def _action_add_all(self) -> None:
        if not self._repo_path:
            self._set_status_msg("[yellow]No repository. Press R to set path.[/yellow]")
            return
        result = _git_add_all(self._repo_path)
        self._set_status_msg(result)
        self._refresh_status()

    def _action_commit(self) -> None:
        if not self._repo_path:
            self._set_status_msg("[yellow]No repository. Press R to set path.[/yellow]")
            return
        self.app.push_screen(
            GitCommitInputScreen(),
            callback=self._on_commit_message,
        )

    def _on_commit_message(self, message: str | None) -> None:
        if not message:
            self._update_footer("Commit cancelled.")
            return
        assert self._repo_path is not None
        result = _git_commit(self._repo_path, message)
        self._set_status_msg(result)
        self._refresh_status()
        self._refresh_history()

    def _action_push(self) -> None:
        if not self._repo_path:
            self._set_status_msg("[yellow]No repository. Press R to set path.[/yellow]")
            return
        self._set_status_msg("[cyan]Pushing…[/cyan]")
        result = _git_push(self._repo_path)
        self._set_status_msg(result)
        self._refresh_status()

    def _action_pull(self) -> None:
        if not self._repo_path:
            self._set_status_msg("[yellow]No repository. Press R to set path.[/yellow]")
            return
        self._set_status_msg("[cyan]Pulling…[/cyan]")
        result = _git_pull(self._repo_path)
        self._set_status_msg(result)
        self._refresh_status()
        self._refresh_history()

    def _action_set_repo(self) -> None:
        current = str(self._repo_path) if self._repo_path else ""
        self.app.push_screen(
            GitRepoPathScreen(current),
            callback=self._on_repo_path,
        )

    def _on_repo_path(self, path_str: str | None) -> None:
        if path_str is None:
            return
        candidate = Path(path_str)
        if candidate.is_dir():
            root = _find_repo_root(candidate)
            if root:
                self._repo_path = root
                self._refresh_all()
            else:
                self._set_status_msg(f"[red]Not a git repo: {path_str}[/red]")
        else:
            self._set_status_msg(f"[red]Directory not found: {path_str}[/red]")
