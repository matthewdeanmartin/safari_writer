"""State models and sample data for Safari Fed."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import TYPE_CHECKING

from mastodon import MastodonError

__all__ = [
    "FOLDER_ORDER",
    "FedPost",
    "SafariFedExitRequest",
    "SafariFedState",
    "build_demo_state",
    "render_post_for_writer",
    "render_thread_for_writer",
]

FOLDER_ORDER = ("Home", "Mentions", "Bookmarks", "Drafts", "Sent", "Deferred")

if TYPE_CHECKING:
    from safari_fed.client import FedSyncResult, SafariFedClient


@dataclass
class FedPost:
    """Local cached representation of a fediverse post."""

    post_id: str
    author: str
    handle: str
    posted_at: str
    age: str
    content_lines: list[str]
    preview_text: str
    thread_title: str
    thread_lines: tuple[str, ...]
    boosts: int = 0
    favourites: int = 0
    replies: int = 0
    tags: tuple[str, ...] = ()
    flags: tuple[str, ...] = ()
    attachments: tuple[str, ...] = ()
    visibility: str = "Public"
    cw: str = "none"
    unread: bool = True
    bookmarked: bool = False
    mention: bool = False
    direct: bool = False
    draft: bool = False
    sent: bool = False
    deferred: bool = False


@dataclass(frozen=True)
class SafariFedExitRequest:
    """Describe a handoff request emitted by Safari Fed."""

    action: str
    document_path: Path | None = None


@dataclass
class FedAccountSession:
    """Per-account cached session data for Safari Fed."""

    account_id: str
    account_label: str
    posts: list[FedPost]
    current_folder: str = "Home"
    view_mode: str = "index"
    selected_index: int = 0
    compose_lines: list[str] = field(default_factory=lambda: [""])
    compose_visibility: str = "Public"
    compose_cw: str = "none"
    reply_to_id: str | None = None
    status_message: str = "Safari Fed ready"
    last_sync_label: str = "Last sync: cached packet"
    client: SafariFedClient | None = field(default=None, repr=False)


@dataclass
class SafariFedState:
    """Mutable state shared by the Safari Fed shell."""

    posts: list[FedPost] = field(default_factory=list)
    current_folder: str = "Home"
    view_mode: str = "index"
    selected_index: int = 0
    compose_lines: list[str] = field(default_factory=lambda: [""])
    compose_visibility: str = "Public"
    compose_cw: str = "none"
    reply_to_id: str | None = None
    status_message: str = "Safari Fed ready"
    last_sync_label: str = "Last sync: cached packet"
    account_label: str = "Demo packet"
    client: SafariFedClient | None = field(default=None, repr=False)
    sessions: dict[str, FedAccountSession] = field(default_factory=dict, repr=False)
    active_account_id: str = "DEMO"

    def visible_posts(self) -> list[FedPost]:
        """Return posts visible in the active folder."""

        if self.current_folder == "Home":
            return [
                post
                for post in self.posts
                if not post.draft and not post.sent and not post.deferred
            ]
        if self.current_folder == "Mentions":
            return [
                post
                for post in self.posts
                if post.mention and not post.draft and not post.deferred
            ]
        if self.current_folder == "Bookmarks":
            return [
                post
                for post in self.posts
                if post.bookmarked and not post.draft and not post.deferred
            ]
        if self.current_folder == "Drafts":
            return [post for post in self.posts if post.draft]
        if self.current_folder == "Sent":
            return [post for post in self.posts if post.sent]
        if self.current_folder == "Deferred":
            return [post for post in self.posts if post.deferred]
        return []

    def current_post(self) -> FedPost | None:
        """Return the currently selected post, if any."""

        posts = self.visible_posts()
        if not posts:
            self.selected_index = 0
            return None
        self.ensure_selection()
        return posts[self.selected_index]

    def ensure_selection(self) -> None:
        """Clamp the selected index to the visible post range."""

        posts = self.visible_posts()
        if not posts:
            self.selected_index = 0
            return
        self.selected_index = max(0, min(self.selected_index, len(posts) - 1))

    def move_selection(self, delta: int) -> None:
        """Move the current selection within the active folder."""

        self.selected_index += delta
        self.ensure_selection()
        self._sync_active_session()

    def cycle_folder(self, delta: int) -> None:
        """Cycle through folders in display order."""

        index = FOLDER_ORDER.index(self.current_folder)
        self.set_folder(FOLDER_ORDER[(index + delta) % len(FOLDER_ORDER)])

    def set_folder(self, folder: str) -> None:
        """Switch to a specific folder."""

        self.current_folder = folder
        self.view_mode = "index"
        self.selected_index = 0
        self._sync_active_session()

    def folder_count(self, folder: str) -> int:
        """Return the visible count for a given folder."""

        original = self.current_folder
        self.current_folder = folder
        count = len(self.visible_posts())
        self.current_folder = original
        return count

    def unread_total(self) -> int:
        """Return the unread count across non-local folders."""

        return sum(
            1
            for post in self.posts
            if post.unread and not post.draft and not post.sent and not post.deferred
        )

    def mention_total(self) -> int:
        """Return the unread mention count."""

        return sum(
            1
            for post in self.posts
            if post.mention and post.unread and not post.deferred
        )

    def toggle_bookmark(self) -> FedPost | None:
        """Toggle bookmark state for the current post."""

        post = self.current_post()
        if post is None:
            self.status_message = "No post selected"
            return None
        desired = not post.bookmarked
        if self.client is not None and not post.post_id.startswith("local-"):
            try:
                if desired:
                    self.client.bookmark(post.post_id)
                else:
                    self.client.unbookmark(post.post_id)
            except (MastodonError, OSError, ValueError) as error:
                self.status_message = f"Bookmark error: {error}"
                self._sync_active_session()
                return None
        post.bookmarked = desired
        self._sync_active_session()
        return post

    def toggle_read(self) -> FedPost | None:
        """Toggle unread state for the current post."""

        post = self.current_post()
        if post is None:
            self.status_message = "No post selected"
            self._sync_active_session()
            return None
        post.unread = not post.unread
        self._sync_active_session()
        return post

    def toggle_deferred(self) -> FedPost | None:
        """Toggle deferred state for the current post."""

        post = self.current_post()
        if post is None:
            self.status_message = "No post selected"
            self._sync_active_session()
            return None
        post.deferred = not post.deferred
        if post.deferred:
            post.unread = False
        self.ensure_selection()
        self._sync_active_session()
        return post

    def create_local_post(self, text: str, draft: bool) -> FedPost:
        """Create a local draft or sent post from compose text."""

        lines = text.splitlines() or [text]
        preview = lines[0]
        post = FedPost(
            post_id=f"local-{len(self.posts) + 1}",
            author="you",
            handle="@you@example.social",
            posted_at="queued locally",
            age="now",
            content_lines=lines,
            preview_text=preview,
            thread_title="Local post",
            thread_lines=("> @you", f"  {preview}"),
            boosts=0,
            favourites=0,
            replies=0,
            tags=("#safari-fed", "#retro", "#mastodon"),
            flags=("local", "queued"),
            attachments=(),
            visibility=self.compose_visibility,
            cw=self.compose_cw,
            unread=not draft,
            draft=draft,
            sent=not draft,
        )
        if self.reply_to_id:
            target = self.find_post(self.reply_to_id)
            if target is not None:
                target.replies += 1
                post.thread_title = f"Reply to {target.author}"
                post.thread_lines = (
                    f">> {target.handle}",
                    f"   {target.preview_text}",
                    ">>> @you@example.social",
                    f"    {preview}",
                )
        self.posts.insert(0, post)
        self.reply_to_id = None
        self.compose_lines = [""]
        self._sync_active_session()
        return post

    def sync_from_api(self, limit: int = 20) -> str:
        """Fetch a fresh packet from Mastodon if credentials are configured."""

        if self.client is None:
            message = "No Mastodon credentials found; using cached demo packet"
            self.status_message = message
            self._sync_active_session()
            return message
        try:
            result = self.client.fetch_sync_result(limit=limit)
        except (MastodonError, OSError, ValueError) as error:
            message = f"Sync error: {error}"
            self.status_message = message
            self._sync_active_session()
            return message
        self._apply_sync_result(result)
        return result.status_message

    def send_compose_post(self) -> str:
        """Send the compose buffer remotely when possible, else queue locally."""

        text = "\n".join(self.compose_lines).strip()
        if not text:
            message = "Cannot send an empty post"
            self.status_message = message
            self._sync_active_session()
            return message
        if self.client is None:
            sent = self.create_local_post(text=text, draft=False)
            self.view_mode = "index"
            self.set_folder("Sent")
            self.focus_post(sent.post_id)
            message = "Post queued locally (no Mastodon credentials)"
            self.status_message = message
            self._sync_active_session()
            return message
        try:
            sent = self.client.send_post(
                text=text,
                visibility=self.compose_visibility,
                reply_to_id=self.reply_to_id,
                spoiler_text=None if self.compose_cw == "none" else self.compose_cw,
            )
        except (MastodonError, OSError, ValueError) as error:
            message = f"Send error: {error}"
            self.status_message = message
            self._sync_active_session()
            return message
        target = self.find_post(self.reply_to_id) if self.reply_to_id else None
        if target is not None:
            target.replies += 1
        self.posts.insert(0, sent)
        self.reply_to_id = None
        self.compose_lines = [""]
        self.view_mode = "index"
        self.set_folder("Sent")
        self.focus_post(sent.post_id)
        message = "Posted to Mastodon"
        self.status_message = message
        self._sync_active_session()
        return message

    def favourite_current(self) -> str:
        """Favourite the current post, optionally calling Mastodon."""

        post = self.current_post()
        if post is None:
            message = "No post selected"
            self.status_message = message
            self._sync_active_session()
            return message
        if self.client is not None and not post.post_id.startswith("local-"):
            try:
                self.client.favourite(post.post_id)
            except (MastodonError, OSError, ValueError) as error:
                message = f"Favourite error: {error}"
                self.status_message = message
                self._sync_active_session()
                return message
        post.favourites += 1
        message = f"Favourite queued for {post.handle}"
        self.status_message = message
        self._sync_active_session()
        return message

    def boost_current(self) -> str:
        """Boost the current post, optionally calling Mastodon."""

        post = self.current_post()
        if post is None:
            message = "No post selected"
            self.status_message = message
            self._sync_active_session()
            return message
        if self.client is not None and not post.post_id.startswith("local-"):
            try:
                self.client.reblog(post.post_id)
            except (MastodonError, OSError, ValueError) as error:
                message = f"Boost error: {error}"
                self.status_message = message
                self._sync_active_session()
                return message
        post.boosts += 1
        message = f"Boost queued for {post.handle}"
        self.status_message = message
        self._sync_active_session()
        return message

    def account_ids(self) -> tuple[str, ...]:
        """Return configured account identifiers in display order."""

        if self.sessions:
            return tuple(self.sessions)
        return (self.active_account_id,)

    def configure_accounts(
        self,
        accounts: dict[str, SafariFedClient | None],
        active_account_id: str | None = None,
    ) -> None:
        """Attach one or more Mastodon accounts to the shared shell state."""

        base_posts = [_clone_post(post) for post in self.posts]
        configured = accounts or {"DEMO": None}
        self.sessions = {}
        for account_id, client in configured.items():
            label = client.identity.label if client is not None else "Demo packet"
            status_message = (
                f"Mastodon ready: {label} (press U to sync)"
                if client is not None
                else "Safari Fed ready"
            )
            last_sync_label = (
                "Last sync: not yet run"
                if client is not None
                else "Last sync: cached packet"
            )
            self.sessions[account_id] = FedAccountSession(
                account_id=account_id,
                account_label=label,
                posts=[_clone_post(post) for post in base_posts],
                current_folder=self.current_folder,
                view_mode=self.view_mode,
                selected_index=0,
                compose_lines=[""],
                compose_visibility="Public",
                compose_cw="none",
                reply_to_id=None,
                status_message=status_message,
                last_sync_label=last_sync_label,
                client=client,
            )
        chosen_account = active_account_id if active_account_id in self.sessions else None
        if chosen_account is None:
            chosen_account = next(iter(self.sessions))
        self.active_account_id = chosen_account
        self._restore_active_session()

    def select_account(self, account_id: str) -> str:
        """Switch the shell to a configured account."""

        if account_id not in self.sessions:
            message = f"Unknown account: {account_id}"
            self.status_message = message
            self._sync_active_session()
            return message
        if account_id == self.active_account_id:
            message = f"Already using {self.account_label}"
            self.status_message = message
            self._sync_active_session()
            return message
        self._sync_active_session()
        self.active_account_id = account_id
        self._restore_active_session()
        message = f"Active account: {self.account_label}"
        self.status_message = message
        self._sync_active_session()
        return message

    def cycle_account(self, delta: int) -> str:
        """Cycle between configured accounts."""

        account_ids = self.account_ids()
        if len(account_ids) <= 1:
            message = f"Only one account configured: {self.account_label}"
            self.status_message = message
            self._sync_active_session()
            return message
        current_index = account_ids.index(self.active_account_id)
        target_index = (current_index + delta) % len(account_ids)
        return self.select_account(account_ids[target_index])

    def select_account_by_number(self, number: int) -> str:
        """Select an account using its one-based index from the UI."""

        account_ids = self.account_ids()
        if number < 1 or number > len(account_ids):
            message = f"No account mapped to {number}"
            self.status_message = message
            self._sync_active_session()
            return message
        return self.select_account(account_ids[number - 1])

    def persist_active_account(self) -> None:
        """Persist transient UI state for the active account."""

        self._sync_active_session()

    def find_post(self, post_id: str | None) -> FedPost | None:
        """Return a post by ID."""

        if post_id is None:
            return None
        for post in self.posts:
            if post.post_id == post_id:
                return post
        return None

    def focus_post(self, post_id: str) -> None:
        """Select a specific post if it is visible."""

        for index, post in enumerate(self.visible_posts()):
            if post.post_id == post_id:
                self.selected_index = index
                self._sync_active_session()
                return

    def _apply_sync_result(self, result: FedSyncResult) -> None:
        overlay = {
            post.post_id: (post.deferred, post.bookmarked)
            for post in self.posts
            if not post.draft
            and not post.sent
            and not post.post_id.startswith("local-")
        }
        local_posts = [
            post
            for post in self.posts
            if post.draft or post.sent or post.post_id.startswith("local-")
        ]
        for post in result.posts:
            deferred, bookmarked = overlay.get(post.post_id, (False, post.bookmarked))
            post.deferred = deferred
            post.bookmarked = post.bookmarked or bookmarked
        self.posts = result.posts + local_posts
        self.account_label = result.account_label
        self.last_sync_label = result.last_sync_label
        self.status_message = result.status_message
        self.ensure_selection()
        self._sync_active_session()

    def _restore_active_session(self) -> None:
        """Load the active account session into the shared view model."""

        session = self.sessions[self.active_account_id]
        self.posts = session.posts
        self.current_folder = session.current_folder
        self.view_mode = session.view_mode
        self.selected_index = session.selected_index
        self.compose_lines = list(session.compose_lines)
        self.compose_visibility = session.compose_visibility
        self.compose_cw = session.compose_cw
        self.reply_to_id = session.reply_to_id
        self.status_message = session.status_message
        self.last_sync_label = session.last_sync_label
        self.account_label = session.account_label
        self.client = session.client
        self.ensure_selection()

    def _sync_active_session(self) -> None:
        """Persist the current view model into the active account session."""

        if self.active_account_id not in self.sessions:
            return
        session = self.sessions[self.active_account_id]
        session.posts = self.posts
        session.current_folder = self.current_folder
        session.view_mode = self.view_mode
        session.selected_index = self.selected_index
        session.compose_lines = list(self.compose_lines)
        session.compose_visibility = self.compose_visibility
        session.compose_cw = self.compose_cw
        session.reply_to_id = self.reply_to_id
        session.status_message = self.status_message
        session.last_sync_label = self.last_sync_label
        session.account_label = self.account_label
        session.client = self.client


def _clone_post(post: FedPost) -> FedPost:
    """Copy a post so account sessions can diverge safely."""

    return replace(
        post,
        content_lines=list(post.content_lines),
        thread_lines=tuple(post.thread_lines),
        tags=tuple(post.tags),
        flags=tuple(post.flags),
        attachments=tuple(post.attachments),
    )


def render_post_for_writer(post: FedPost) -> str:
    """Render a post as plain text suitable for Safari Writer."""

    lines = [
        f"Safari Fed export: {post.thread_title}",
        f"Author: {post.handle}",
        f"Posted: {post.posted_at}",
        f"Visibility: {post.visibility}",
        f"Tags: {' '.join(post.tags) if post.tags else 'none'}",
        "",
        *post.content_lines,
    ]
    if post.attachments:
        lines.extend(["", *post.attachments])
    return "\n".join(lines)


def render_thread_for_writer(post: FedPost) -> str:
    """Render a thread as plain text suitable for Safari Writer."""

    return "\n".join(
        [
            f"Safari Fed thread export: {post.thread_title}",
            "",
            *post.thread_lines,
            "",
            "Selected post:",
            *post.content_lines,
        ]
    )


def build_demo_state(start_folder: str = "Home") -> SafariFedState:
    """Build seeded local-first demo state for the Safari Fed shell."""

    posts = [
        FedPost(
            post_id="p1",
            author="alice",
            handle="@alice@example.social",
            posted_at="2026-03-08 15:18",
            age="2m",
            content_lines=[
                "Python packaging is weird again, but at least pyproject.toml is",
                "better than the old setup.py treasure hunt.",
            ],
            preview_text="Python packaging is weird again...",
            thread_title="Packaging again",
            thread_lines=(
                "> @alice",
                "  Python packaging is weird again...",
                ">> @bob",
                "   Editable installs are the real archaeology layer.",
            ),
            boosts=14,
            favourites=22,
            replies=5,
            tags=("#python", "#packaging"),
            flags=("unread", "thread starter"),
            unread=True,
        ),
        FedPost(
            post_id="p2",
            author="bob",
            handle="@bob@example.social",
            posted_at="2026-03-08 15:20",
            age="5m",
            content_lines=[
                "Anyone know an AtariWriter clone? I want the menus and keybindings,",
                "not just a generic text editor in curses.",
            ],
            preview_text="Anyone know an AtariWriter clone?",
            thread_title="AtariWriter clone discussion",
            thread_lines=(
                "> @bob",
                "  Anyone know an AtariWriter clone?",
                ">> @matthew",
                "   I want one with real menu vibes.",
                ">>> @carol",
                "    You might want Pine-style indexes too.",
            ),
            boosts=2,
            favourites=11,
            replies=12,
            tags=("#retcomputing", "#python"),
            flags=("thread starter",),
            unread=False,
        ),
        FedPost(
            post_id="p3",
            author="carol",
            handle="@carol@retro.social",
            posted_at="2026-03-08 15:26",
            age="9m",
            content_lines=[
                "Long thread: static site generation feels simple until you decide",
                "asset pipelines are a personality trait.",
            ],
            preview_text="Long thread: static site generation...",
            thread_title="Static site thread",
            thread_lines=(
                "> @carol",
                "  Long thread: static site generation...",
                ">> @dan",
                "   I still just write HTML and feel fine.",
            ),
            boosts=8,
            favourites=30,
            replies=18,
            tags=("#web", "#buildtools"),
            flags=("bookmarked",),
            unread=True,
            bookmarked=True,
        ),
        FedPost(
            post_id="p4",
            author="dan",
            handle="@dan@example.net",
            posted_at="2026-03-08 15:31",
            age="14m",
            content_lines=[
                "New blog post on Mastodon clients: thread handling matters more than",
                "infinite scroll, and local cache is a feature not a hack.",
            ],
            preview_text="New blog post on Mastodon clients",
            thread_title="Client design notes",
            thread_lines=(
                "> @dan",
                "  New blog post on Mastodon clients...",
            ),
            boosts=0,
            favourites=3,
            replies=1,
            tags=("#mastodon", "#ux"),
            flags=("link",),
            attachments=("[LINK] https://example.net/blog/mastodon-clients",),
            unread=False,
        ),
        FedPost(
            post_id="p5",
            author="erin",
            handle="@erin@example.social",
            posted_at="2026-03-08 15:34",
            age="17m",
            content_lines=[
                "@you@example.social You were mentioned in a thread about queue-based",
                "reading mode. It turns out mailbox metaphors still work.",
            ],
            preview_text="You were mentioned in a thread",
            thread_title="Queue mode mention",
            thread_lines=(
                "> @erin",
                "  @you@example.social You were mentioned...",
                ">> @you@example.social",
                "   Queue mode is the whole point.",
            ),
            boosts=1,
            favourites=6,
            replies=4,
            tags=("#mastodon", "#retrocomputing"),
            flags=("mention",),
            mention=True,
            unread=True,
        ),
        FedPost(
            post_id="p6",
            author="fran",
            handle="@fran@quiet.example",
            posted_at="2026-03-08 15:40",
            age="23m",
            content_lines=[
                "Direct note: keep media optional and the timeline text-first.",
                "That is how the app stays usable on slow days and small screens.",
            ],
            preview_text="Direct note: keep media optional...",
            thread_title="Private note",
            thread_lines=(
                "> @fran",
                "  Direct note: keep media optional...",
            ),
            boosts=0,
            favourites=1,
            replies=0,
            flags=("direct",),
            visibility="Private",
            direct=True,
            unread=True,
        ),
        FedPost(
            post_id="p7",
            author="you",
            handle="@you@example.social",
            posted_at="saved locally",
            age="draft",
            content_lines=[
                "Draft: Safari Fed should export selected threads straight into Writer",
                "so a blog draft can start from a curated quote packet.",
            ],
            preview_text="Draft: export selected threads to Writer",
            thread_title="Draft note",
            thread_lines=(
                "> @you@example.social",
                "  Draft: Safari Fed should export selected threads...",
            ),
            boosts=0,
            favourites=0,
            replies=0,
            tags=("#draft",),
            flags=("draft",),
            unread=False,
            draft=True,
        ),
        FedPost(
            post_id="p8",
            author="you",
            handle="@you@example.social",
            posted_at="queued yesterday",
            age="sent",
            content_lines=[
                "Sent note: the fediverse gets more manageable when you treat it as",
                "a message packet instead of an endless feed.",
            ],
            preview_text="Sent note: the fediverse gets more manageable...",
            thread_title="Sent note",
            thread_lines=(
                "> @you@example.social",
                "  Sent note: the fediverse gets more manageable...",
            ),
            boosts=0,
            favourites=2,
            replies=1,
            tags=("#sent",),
            flags=("sent",),
            unread=False,
            sent=True,
        ),
        FedPost(
            post_id="p9",
            author="gwen",
            handle="@gwen@archive.example",
            posted_at="deferred packet",
            age="later",
            content_lines=[
                "Deferred: save this long thread about packet readers and bulletin",
                "boards for a slower afternoon.",
            ],
            preview_text="Deferred: save this long thread for later",
            thread_title="Deferred bulletin idea",
            thread_lines=(
                "> @gwen",
                "  Deferred: save this long thread for later...",
            ),
            boosts=5,
            favourites=7,
            replies=3,
            tags=("#archive",),
            flags=("deferred",),
            unread=False,
            deferred=True,
        ),
    ]
    state = SafariFedState(posts=posts)
    if start_folder in FOLDER_ORDER:
        state.current_folder = start_folder
    state.configure_accounts({"DEMO": None}, active_account_id="DEMO")
    state.ensure_selection()
    return state
