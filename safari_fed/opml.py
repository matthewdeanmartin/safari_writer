"""OPML export support for Safari Fed followed-profile feed discovery."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from html import escape
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urljoin, urlparse

import httpx

from safari_fed.client import SafariFedClient

__all__ = [
    "DEFAULT_MAX_ACCOUNTS",
    "DEFAULT_MAX_FEEDS",
    "FeedSubscription",
    "WebDocument",
    "build_opml_document",
    "default_opml_export_path",
    "export_followed_feeds_to_opml",
]

DEFAULT_MAX_ACCOUNTS = 100
DEFAULT_MAX_FEEDS = 20

_FEED_CONTENT_TYPES = (
    "application/rss+xml",
    "application/atom+xml",
    "application/xml",
    "text/xml",
)
_COMMON_FEED_PATHS = (
    "feed",
    "rss",
    "rss.xml",
    "feed.xml",
    "atom.xml",
    "index.xml",
    "feeds/posts/default",
)
_HREF_RE = re.compile(r"""href\s*=\s*["']([^"'<> ]+)["']""", re.IGNORECASE)

# Known fediverse server software domains and patterns.
# Profile URLs on these instances are NOT personal blogs.
_FEDIVERSE_DOMAINS = frozenset({
    "mastodon.social",
    "mastodon.online",
    "mastodon.world",
    "mstdn.social",
    "mstdn.jp",
    "mas.to",
    "fosstodon.org",
    "hachyderm.io",
    "infosec.exchange",
    "tech.lgbt",
    "toot.community",
    "universeodon.com",
    "c.im",
    "sfba.social",
    "aus.social",
    "social.coop",
    "kolektiva.social",
    "mathstodon.xyz",
    "scholar.social",
    "masto.ai",
    "sciences.social",
    "sigmoid.social",
    "pixel.kitchen",
    "octodon.social",
    "ruby.social",
    "phpc.social",
    "chaos.social",
    "nrw.social",
    "social.linux.pizza",
    "social.tchncs.de",
    "ioc.exchange",
})

# Patterns that mark a URL as a fediverse profile (not a personal blog).
_FEDIVERSE_PATH_PATTERNS = (
    re.compile(r"^/@[^/]+/?$"),          # mastodon-style /@user
    re.compile(r"^/users/[^/]+/?$"),      # ActivityPub /users/user
)


def _is_fediverse_profile_url(url: str) -> bool:
    """Return True if *url* points to a fediverse profile, not a blog."""
    parsed = urlparse(url)
    host = parsed.hostname or ""
    # Exact domain match
    if host in _FEDIVERSE_DOMAINS:
        return True
    # Sub-domains of known instances (e.g. www.mastodon.social)
    for domain in _FEDIVERSE_DOMAINS:
        if host.endswith(f".{domain}"):
            return True
    # Any domain with a /@user or /users/user path pattern
    path = parsed.path
    for pat in _FEDIVERSE_PATH_PATTERNS:
        if pat.match(path):
            return True
    return False


@dataclass(frozen=True)
class WebDocument:
    """Fetched web document metadata used for feed discovery."""

    url: str
    text: str
    content_type: str = ""


@dataclass(frozen=True)
class FeedSubscription:
    """One OPML outline row."""

    title: str
    xml_url: str
    html_url: str
    account_handle: str = ""


class _FeedLinkParser(HTMLParser):
    """Extract page title and alternate feed URLs from HTML."""

    def __init__(self) -> None:
        super().__init__()
        self.title = ""
        self.feed_links: list[str] = []
        self._in_title = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = {name.lower(): (value or "") for name, value in attrs}
        if tag.lower() == "title":
            self._in_title = True
            return
        if tag.lower() != "link":
            return
        rel = attr_map.get("rel", "").lower()
        href = attr_map.get("href", "").strip()
        link_type = attr_map.get("type", "").lower()
        if "alternate" not in rel or not href:
            return
        if any(content_type in link_type for content_type in _FEED_CONTENT_TYPES):
            self.feed_links.append(href)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.title += data


def default_opml_export_path(account_name: str | None = None) -> Path:
    """Return the default OPML export path in Safari Fed's config folder."""

    from safari_fed.app import fed_config_dir

    suffix = (
        ""
        if not account_name
        else "-" + "".join(ch.lower() if ch.isalnum() else "-" for ch in account_name)
    ).strip("-")
    filename = "fed-feeds.opml" if not suffix else f"fed-feeds-{suffix}.opml"
    return fed_config_dir() / filename


def build_opml_document(
    subscriptions: list[FeedSubscription],
    *,
    title: str = "Safari Fed feeds",
) -> str:
    """Render an OPML document for the discovered subscriptions."""

    created = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S UTC")
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<opml version="2.0">',
        "  <head>",
        f"    <title>{escape(title)}</title>",
        f"    <dateCreated>{escape(created)}</dateCreated>",
        "  </head>",
        "  <body>",
    ]
    for item in subscriptions:
        lines.append(
            "    "
            + (
                f'<outline text="{escape(item.title)}" title="{escape(item.title)}" '
                f'type="rss" xmlUrl="{escape(item.xml_url)}" '
                f'htmlUrl="{escape(item.html_url)}" />'
            )
        )
    lines.extend(["  </body>", "</opml>"])
    return "\n".join(lines) + "\n"


def export_followed_feeds_to_opml(
    fed_client: SafariFedClient,
    output_path: Path,
    *,
    fetcher: callable | None = None,
    max_accounts: int = DEFAULT_MAX_ACCOUNTS,
    max_feeds: int = DEFAULT_MAX_FEEDS,
) -> list[FeedSubscription]:
    """Discover followed-profile feeds and write them as OPML."""

    fetch = _fetch_document if fetcher is None else fetcher
    accounts = _load_followed_accounts(fed_client, limit=max_accounts)
    subscriptions: list[FeedSubscription] = []
    seen_xml_urls: set[str] = set()

    for account in accounts:
        if len(subscriptions) >= max_feeds:
            break
        for candidate_url in _candidate_urls_for_account(account):
            subscription = _discover_subscription(
                candidate_url,
                account=account,
                fetcher=fetch,
            )
            if subscription is None or subscription.xml_url in seen_xml_urls:
                continue
            seen_xml_urls.add(subscription.xml_url)
            subscriptions.append(subscription)
            if len(subscriptions) >= max_feeds:
                break

    subscriptions.sort(key=lambda item: item.title.lower())
    output_path.parent.mkdir(parents=True, exist_ok=True)
    title = f"Safari Fed feeds ({fed_client.identity.name})"
    output_path.write_text(build_opml_document(subscriptions, title=title), encoding="utf-8")
    return subscriptions


def _load_followed_accounts(
    fed_client: SafariFedClient,
    *,
    limit: int,
) -> list[Mapping[str, Any]]:
    account = _as_mapping(fed_client.client.account_verify_credentials())
    account_id = account.get("id")
    if account_id in {None, ""}:
        return []
    rows = fed_client.client.account_following(account_id, limit=limit)
    return [_as_mapping(row) for row in rows]


def _candidate_urls_for_account(account: Mapping[str, Any]) -> list[str]:
    seen: set[str] = set()
    candidates: list[str] = []
    # Prioritise explicit website and profile fields over the profile URL,
    # which on Mastodon instances points to the fediverse profile (not a blog).
    for raw in (
        account.get("website"),
        account.get("note"),
    ):
        _collect_candidate_url(raw, seen, candidates)
    for field in account.get("fields", []):
        if isinstance(field, Mapping):
            _collect_candidate_url(field.get("value"), seen, candidates)
            _collect_candidate_url(field.get("name"), seen, candidates)
    # Only add the profile URL / URI as a last resort, and skip it when it
    # clearly points to a fediverse instance rather than a personal site.
    for raw in (account.get("url"), account.get("uri")):
        if raw and not _is_fediverse_profile_url(str(raw)):
            _collect_candidate_url(raw, seen, candidates)
    return candidates


def _collect_candidate_url(value: object, seen: set[str], candidates: list[str]) -> None:
    if not value:
        return
    for url in _extract_urls(str(value)):
        if url not in seen:
            seen.add(url)
            candidates.append(url)


def _extract_urls(value: str) -> list[str]:
    urls = _HREF_RE.findall(value)
    urls.extend(re.findall(r"https?://[^\s<>\"]+", value))
    cleaned: list[str] = []
    for url in urls:
        trimmed = url.rstrip(").,;!?")
        parsed = urlparse(trimmed)
        if parsed.scheme in {"http", "https"} and parsed.netloc:
            cleaned.append(trimmed)
    return cleaned


def _discover_subscription(
    url: str,
    *,
    account: Mapping[str, Any],
    fetcher: callable,
) -> FeedSubscription | None:
    direct_document = fetcher(url)
    if direct_document is None:
        return None
    if _looks_like_feed(direct_document):
        return FeedSubscription(
            title=_subscription_title(account, fallback=url),
            xml_url=direct_document.url,
            html_url=url,
            account_handle=_account_handle(account),
        )

    parsed = _FeedLinkParser()
    parsed.feed(direct_document.text)
    feed_links = [
        urljoin(direct_document.url, href)
        for href in parsed.feed_links
        if not _is_fediverse_profile_url(urljoin(direct_document.url, href))
    ]

    if not feed_links:
        for suffix in _COMMON_FEED_PATHS:
            feed_url = _join_feed_candidate(direct_document.url, suffix)
            discovered = fetcher(feed_url)
            if discovered is not None and _looks_like_feed(discovered):
                feed_links.append(discovered.url)
                break

    if not feed_links:
        return None

    page_title = parsed.title.strip()
    return FeedSubscription(
        title=_subscription_title(account, fallback=page_title or direct_document.url),
        xml_url=feed_links[0],
        html_url=direct_document.url,
        account_handle=_account_handle(account),
    )


def _subscription_title(account: Mapping[str, Any], fallback: str) -> str:
    display_name = str(account.get("display_name") or "").strip()
    handle = _account_handle(account)
    if display_name and handle:
        return f"{display_name} ({handle})"
    return display_name or handle or fallback


def _account_handle(account: Mapping[str, Any]) -> str:
    acct = str(account.get("acct") or account.get("username") or "").strip()
    if not acct:
        return ""
    return acct if acct.startswith("@") else f"@{acct}"


def _join_feed_candidate(base_url: str, suffix: str) -> str:
    base = base_url.rstrip("/") + "/"
    return urljoin(base, suffix)


def _looks_like_feed(document: WebDocument) -> bool:
    content_type = document.content_type.lower()
    if any(feed_type in content_type for feed_type in _FEED_CONTENT_TYPES):
        return True
    snippet = document.text.lstrip().lower()[:400]
    return "<rss" in snippet or "<feed" in snippet or "<rdf:rdf" in snippet


def _fetch_document(url: str) -> WebDocument | None:
    try:
        response = httpx.get(url, timeout=10, follow_redirects=True)
        response.raise_for_status()
    except httpx.HTTPError:
        return None
    return WebDocument(
        url=str(response.url),
        text=response.text,
        content_type=response.headers.get("content-type", ""),
    )


def _as_mapping(value: object) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return value
    if hasattr(value, "items"):
        return dict(value.items())
    if hasattr(value, "__dict__"):
        return dict(vars(value))
    raise ValueError(f"Expected mapping-compatible row, got {type(value)!r}")
