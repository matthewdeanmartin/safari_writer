"""Basic Mastodon API support for Safari Fed."""

from __future__ import annotations

import re
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import datetime, timezone
from html import unescape
from typing import Any, Mapping, cast

from mastodon import Mastodon

from safari_fed.config import (MastodonIdentity, load_default_identity,
                               load_mastodon_identities)
from safari_fed.state import FedPost

__all__ = [
    "FedSyncResult",
    "SafariFedClient",
    "load_clients_from_env",
    "load_client_from_env",
]

_TAG_RE = re.compile(r"<[^>]+>")
_BREAK_RE = re.compile(r"<br\s*/?>|</p>|</div>|</li>", re.IGNORECASE)
_LINE_RE = re.compile(r"\r\n?|\n")


@dataclass(frozen=True)
class FedSyncResult:
    """Normalized feed snapshot returned from Mastodon."""

    posts: list[FedPost]
    account_label: str
    last_sync_label: str
    status_message: str


class SafariFedClient:
    """Thin wrapper around mastodon-py for Safari Fed."""

    def __init__(
        self,
        identity: MastodonIdentity,
        mastodon_factory: Callable[..., Mastodon] = Mastodon,
    ) -> None:
        self.identity = identity
        self.client = mastodon_factory(
            client_id=identity.client_id,
            client_secret=identity.client_secret,
            access_token=identity.access_token,
            api_base_url=identity.base_url,
        )

    def fetch_sync_result(self, limit: int = 20) -> FedSyncResult:
        """Fetch the main feed surfaces Safari Fed currently supports."""

        account = self._as_mapping(self.client.account_verify_credentials())
        account_label = self._account_label(account)
        home_rows = self._as_list(self.client.timeline_home(limit=limit))
        bookmark_rows = self._as_list(self.client.bookmarks(limit=limit))
        notification_rows = self._as_list(self.client.notifications(limit=limit))

        posts_by_id: dict[str, FedPost] = {}
        ordered_ids: list[str] = []
        mention_count = 0
        extra_notification_count = 0

        for row in home_rows:
            post = self._status_to_post(row)
            ordered_ids.append(self._merge_post(posts_by_id, post))

        for row in bookmark_rows:
            post = self._status_to_post(row, bookmarked=True)
            ordered_ids.append(self._merge_post(posts_by_id, post))

        for row in notification_rows:
            notification = self._as_mapping(row)
            status = notification.get("status")
            notification_type = str(notification.get("type", ""))
            if status is None:
                extra_notification_count += 1
                continue
            if notification_type == "mention":
                mention_count += 1
                post = self._status_to_post(status, mention=True)
                ordered_ids.append(self._merge_post(posts_by_id, post))
                continue
            extra_notification_count += 1

        seen: set[str] = set()
        ordered_posts: list[FedPost] = []
        for post_id in ordered_ids:
            if post_id in seen:
                continue
            seen.add(post_id)
            ordered_posts.append(posts_by_id[post_id])

        summary = (
            f"Synced {len(home_rows)} home, {mention_count} mentions, "
            f"{len(bookmark_rows)} bookmarks, {extra_notification_count} notices"
        )
        return FedSyncResult(
            posts=ordered_posts,
            account_label=account_label,
            last_sync_label=f"Last sync: {self.identity.label}",
            status_message=summary,
        )

    def send_post(
        self,
        text: str,
        visibility: str = "public",
        reply_to_id: str | None = None,
        spoiler_text: str | None = None,
    ) -> FedPost:
        """Post a status and normalize the returned row."""

        result = self.client.status_post(
            status=text,
            visibility=visibility.lower(),
            in_reply_to_id=reply_to_id,
            spoiler_text=spoiler_text or None,
        )
        post = self._status_to_post(result)
        post.sent = True
        post.unread = False
        return post

    def favourite(self, post_id: str) -> None:
        """Favourite a status."""

        self.client.status_favourite(post_id)

    def reblog(self, post_id: str) -> None:
        """Boost a status."""

        self.client.status_reblog(post_id)

    def bookmark(self, post_id: str) -> None:
        """Bookmark a status."""

        self.client.status_bookmark(post_id)

    def unbookmark(self, post_id: str) -> None:
        """Remove a bookmark from a status."""

        self.client.status_unbookmark(post_id)

    def _merge_post(self, posts_by_id: dict[str, FedPost], post: FedPost) -> str:
        post_id = post.post_id
        if post_id not in posts_by_id:
            posts_by_id[post_id] = post
            return post_id
        existing = posts_by_id[post_id]
        existing.bookmarked = existing.bookmarked or post.bookmarked
        existing.mention = existing.mention or post.mention
        existing.unread = existing.unread or post.unread
        if post.flags:
            merged_flags = tuple(dict.fromkeys(existing.flags + post.flags))
            existing.flags = merged_flags
        return post_id

    def _status_to_post(
        self,
        row: object,
        *,
        mention: bool = False,
        bookmarked: bool = False,
    ) -> FedPost:
        data = self._status_payload(row)
        post_id = str(data.get("id", ""))
        account = self._as_mapping(data.get("account", {}))
        display_name = str(account.get("display_name") or account.get("username") or "")
        acct = str(account.get("acct") or account.get("username") or "unknown")
        handle = f"@{acct}" if not acct.startswith("@") else acct
        text_lines = self._status_lines(data)
        preview = next((line for line in text_lines if line.strip()), "(media only)")
        tags = tuple(
            f"#{self._as_mapping(tag).get('name')}"
            for tag in self._as_list(data.get("tags", []))
        )
        attachments = tuple(self._attachment_lines(data))
        visibility = str(data.get("visibility", "public")).capitalize()
        cw = str(data.get("spoiler_text") or "none")
        created_at = data.get("created_at")
        flags = []
        if mention:
            flags.append("mention")
        if bookmarked:
            flags.append("bookmark")
        if visibility.lower() in {"direct", "private"}:
            flags.append("private")
        return FedPost(
            post_id=post_id,
            author=display_name or handle,
            handle=handle,
            posted_at=self._format_posted_at(created_at),
            age=self._format_age(created_at),
            content_lines=text_lines,
            preview_text=preview,
            thread_title=preview,
            thread_lines=(
                f"> {handle}",
                f"  {preview}",
            ),
            boosts=int(data.get("reblogs_count") or 0),
            favourites=int(data.get("favourites_count") or 0),
            replies=int(data.get("replies_count") or 0),
            tags=tags,
            flags=tuple(flags),
            attachments=attachments,
            visibility=visibility,
            cw=cw,
            unread=True,
            bookmarked=bookmarked,
            mention=mention,
            direct=visibility.lower() in {"direct", "private"},
        )

    def _status_payload(self, row: object) -> Mapping[str, Any]:
        data = self._as_mapping(row)
        if data.get("reblog"):
            nested = self._as_mapping(data["reblog"])
            reblogger = self._as_mapping(data.get("account", {}))
            boosted_by = str(reblogger.get("acct") or reblogger.get("username") or "")
            nested = dict(nested)
            content = self._plain_text(nested.get("content", ""))
            nested["content"] = f"Boosted by @{boosted_by}\n{content}".strip()
            return nested
        return data

    def _attachment_lines(self, status: Mapping[str, Any]) -> list[str]:
        rendered: list[str] = []
        for attachment in self._as_list(status.get("media_attachments", [])):
            media = self._as_mapping(attachment)
            kind = str(media.get("type", "media")).upper()
            description = str(
                media.get("description") or media.get("text_url") or ""
            ).strip()
            label = f"[{kind}]"
            rendered.append(f"{label} {description}".strip())
        return rendered

    def _status_lines(self, status: Mapping[str, Any]) -> list[str]:
        text = self._plain_text(status.get("content", ""))
        spoiler_text = str(status.get("spoiler_text") or "").strip()
        if spoiler_text:
            text = f"CW: {spoiler_text}\n{text}".strip()
        lines = [line.rstrip() for line in _LINE_RE.split(text)]
        cleaned = [line for line in lines if line.strip()]
        return cleaned or ["(no text body)"]

    def _plain_text(self, value: object) -> str:
        text = str(value or "")
        text = _BREAK_RE.sub("\n", text)
        text = _TAG_RE.sub("", text)
        return unescape(text).strip()

    def _account_label(self, account: Mapping[str, Any]) -> str:
        acct = str(account.get("acct") or account.get("username") or self.identity.name)
        return f"@{acct}" if not acct.startswith("@") else acct

    def _format_posted_at(self, value: object) -> str:
        from safari_writer.locale_info import format_datetime

        parsed = self._parse_datetime(value)
        if parsed is None:
            return "unknown"
        return format_datetime(parsed.astimezone(timezone.utc), style="short") + " UTC"

    def _format_age(self, value: object) -> str:
        parsed = self._parse_datetime(value)
        if parsed is None:
            return "now"
        seconds = max(0, int((datetime.now(timezone.utc) - parsed).total_seconds()))
        if seconds < 60:
            return f"{seconds}s"
        if seconds < 3600:
            return f"{seconds // 60}m"
        if seconds < 86400:
            return f"{seconds // 3600}h"
        return f"{seconds // 86400}d"

    def _parse_datetime(self, value: object) -> datetime | None:
        if isinstance(value, datetime):
            if value.tzinfo is None:
                return value.replace(tzinfo=timezone.utc)
            return value.astimezone(timezone.utc)
        if not value:
            return None
        text = str(value).replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(text)
        except ValueError:
            return None
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)

    def _as_list(self, value: object) -> list[object]:
        if value is None:
            return []
        if isinstance(value, Iterable) and not isinstance(value, (str, bytes)):
            return list(cast(Iterable[object], value))
        raise ValueError(
            f"Expected iterable Mastodon row collection, got {type(value)!r}"
        )

    def _as_mapping(self, value: object) -> Mapping[str, Any]:
        if isinstance(value, Mapping):
            return value
        if hasattr(value, "items"):
            return dict(cast(Any, value).items())
        if hasattr(value, "__dict__"):
            return dict(vars(value))
        raise ValueError(
            f"Expected mapping-compatible Mastodon row, got {type(value)!r}"
        )


def load_client_from_env() -> SafariFedClient | None:
    """Build a Safari Fed client from the configured environment."""

    identity = load_default_identity()
    if identity is None:
        return None
    return SafariFedClient(identity)


def load_clients_from_env() -> tuple[dict[str, SafariFedClient], str | None]:
    """Build Safari Fed clients for every configured Mastodon identity."""

    identities = load_mastodon_identities()
    if not identities:
        return {}, None
    clients = {
        name: SafariFedClient(identity) for name, identity in sorted(identities.items())
    }
    default_identity = load_default_identity()
    default_name = default_identity.name if default_identity is not None else None
    if default_name not in clients:
        default_name = next(iter(clients))
    return clients, default_name
