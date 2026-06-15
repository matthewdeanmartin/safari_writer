"""Integration tests: safari_fed's Mastodon client against a real HTTP mock.

These boot the ``mastodon_mock`` package (published on PyPI) as a uvicorn server
on a free port and point ``SafariFedClient`` at it — no live instance, no API
keys. The mock is a *stateful* simulation (a status you POST shows up on the next
read), so safari_fed's read **and** write surfaces are exercised end to end: it
is safe to test writes here precisely because nothing leaves localhost.

The module self-skips on Python < 3.13 (mastodon_mock's ``requires-python``) or
if ``mastodon_mock`` is not installed (install ``mastodon_mock[test]``). The
free-port/uvicorn/threading boilerplate this module used to hand-roll now lives
in ``mastodon_mock.testing.MockServer``.

Run just this module::

    uv run pytest test_integration/test_fed_against_mock.py
"""

from __future__ import annotations

import sys
from collections.abc import Iterator

import pytest

if sys.version_info < (3, 13):
    pytest.skip(
        "mastodon_mock requires Python >= 3.13; skipping fed mock integration suite",
        allow_module_level=True,
    )

pytest.importorskip(
    "mastodon_mock",
    reason="install mastodon_mock[test] to run these tests",
)

from mastodon_mock.config import (  # noqa: E402
    SeedAccount,
    SeedConfig,
    SeedFollow,
    SeedStatus,
)
from mastodon_mock.testing import MockServer  # noqa: E402

from safari_fed.client import SafariFedClient  # noqa: E402
from safari_fed.config import MastodonIdentity  # noqa: E402

ME_TOKEN = "safari_token"
FRIEND_TOKEN = "friend_token"

# A seed rich enough for the sync surfaces safari_fed reads: "me" follows
# "friend", who has a couple of statuses, so the home timeline is non-empty.
INTEGRATION_SEED = SeedConfig(
    accounts=[
        SeedAccount(username="me", display_name="Safari User", access_token=ME_TOKEN),
        SeedAccount(username="friend", display_name="A Friend", access_token=FRIEND_TOKEN),
    ],
    follows=[SeedFollow(follower="me", following="friend")],
    statuses=[
        SeedStatus(account="friend", text="hello from the timeline #retro"),
        SeedStatus(account="friend", text="a second friendly post"),
    ],
)


@pytest.fixture(scope="module")
def mock_server_url() -> Iterator[str]:
    """Module-scoped mock server backed by the integration seed.

    ``MockServer`` owns the free port, readiness wait, and teardown.
    """
    with MockServer(seed=INTEGRATION_SEED) as server:
        yield server.base_url


def _identity(base_url: str, name: str = "MAIN", token: str = ME_TOKEN) -> MastodonIdentity:
    return MastodonIdentity(
        name=name,
        base_url=base_url,
        access_token=token,
        client_id="integration-client-id",
        client_secret="integration-client-secret",
    )


@pytest.fixture
def fed_client(mock_server_url: str) -> SafariFedClient:
    """A SafariFedClient (as "me") pointed at the mock."""
    return SafariFedClient(_identity(mock_server_url))


@pytest.fixture
def friend_client(mock_server_url: str) -> SafariFedClient:
    """A second client (as "friend") to set up state the "me" client reads."""
    return SafariFedClient(_identity(mock_server_url, name="FRIEND", token=FRIEND_TOKEN))


# --- Read surface -----------------------------------------------------------


def test_fetch_sync_result_shape(fed_client: SafariFedClient) -> None:
    result = fed_client.fetch_sync_result(limit=20)
    assert result.account_label == "@me"
    assert result.last_sync_label.startswith("Last sync:")
    assert "Synced" in result.status_message
    # "me" follows "friend" who has two seeded statuses → home is non-empty.
    assert result.posts
    for post in result.posts:
        assert post.post_id
        assert post.handle.startswith("@")
        assert post.content_lines
        assert post.preview_text


def test_fetch_sync_result_renders_tags(fed_client: SafariFedClient) -> None:
    result = fed_client.fetch_sync_result(limit=20)
    all_tags = {tag for post in result.posts for tag in post.tags}
    # The seeded "#retro" status should surface its tag through the renderer.
    assert "#retro" in all_tags


def test_mention_notification_is_flagged(
    fed_client: SafariFedClient, friend_client: SafariFedClient
) -> None:
    """A friend's @mention surfaces in sync as a mention-flagged post.

    Exercises the notifications→mention branch of fetch_sync_result and the
    summary counter.
    """
    sent = friend_client.send_post("hey @me look at this specific thing", visibility="public")
    result = fed_client.fetch_sync_result(limit=40)
    mentions = [post for post in result.posts if post.mention]
    assert mentions, "the @mention should appear as a mention-flagged post"
    # The specific mention we just created is among them (robust to other tests
    # on the shared module server having created mentions too).
    assert sent.post_id in {post.post_id for post in mentions}


def test_reblog_is_rendered_with_boosted_by(
    fed_client: SafariFedClient, friend_client: SafariFedClient
) -> None:
    """A boost in the home timeline renders the 'Boosted by @…' prefix.

    Drives the nested-reblog payload branch of _status_payload against a reblog
    row the mock actually creates.
    """
    mine = fed_client.send_post("original to be boosted", visibility="public")
    friend_client.reblog(mine.post_id)

    result = fed_client.fetch_sync_result(limit=40)
    boosted = [
        post
        for post in result.posts
        if any("Boosted by @friend" in line for line in post.content_lines)
    ]
    assert boosted, "friend's boost should render with a 'Boosted by' prefix"


def test_direct_visibility_is_flagged_private(fed_client: SafariFedClient) -> None:
    """Direct/private posts get the 'private' flag and direct=True."""
    sent = fed_client.send_post("a private note", visibility="direct")
    assert sent.visibility == "Direct"
    assert sent.direct is True
    assert "private" in sent.flags


# --- Write surface (safe: localhost mock only) ------------------------------


def test_send_post_round_trips_into_timeline(fed_client: SafariFedClient) -> None:
    sent = fed_client.send_post("posting from safari fed #retro", visibility="public")
    assert sent.sent is True
    assert sent.unread is False
    assert sent.post_id
    assert any("posting from safari fed" in line for line in sent.content_lines)

    # It shows up on a subsequent sync (the post is by "me", so home includes it).
    result = fed_client.fetch_sync_result(limit=40)
    assert sent.post_id in {post.post_id for post in result.posts}


def test_send_reply_threads_and_carries_visibility(
    fed_client: SafariFedClient, friend_client: SafariFedClient
) -> None:
    parent = friend_client.send_post("anyone around?", visibility="public")
    reply = fed_client.send_post(
        "yes, hello!", visibility="unlisted", reply_to_id=parent.post_id
    )
    assert reply.post_id
    assert reply.visibility == "Unlisted"


def test_send_post_with_spoiler_text(fed_client: SafariFedClient) -> None:
    sent = fed_client.send_post(
        "the spoiler body", visibility="public", spoiler_text="CW here"
    )
    # safari_fed prefixes the content-warning into the rendered lines.
    assert sent.cw == "CW here"
    assert any("CW: CW here" in line for line in sent.content_lines)


def test_favourite_then_reblog(fed_client: SafariFedClient, friend_client: SafariFedClient) -> None:
    target = friend_client.send_post("boost me maybe", visibility="public")
    # These return None; success is "no exception" against a real HTTP server.
    fed_client.favourite(target.post_id)
    fed_client.reblog(target.post_id)


def test_bookmark_then_appears_in_sync_then_unbookmark(
    fed_client: SafariFedClient, friend_client: SafariFedClient
) -> None:
    target = friend_client.send_post("bookmark this please", visibility="public")

    fed_client.bookmark(target.post_id)
    result = fed_client.fetch_sync_result(limit=40)
    bookmarked = {post.post_id for post in result.posts if post.bookmarked}
    assert target.post_id in bookmarked

    fed_client.unbookmark(target.post_id)
    after = fed_client.fetch_sync_result(limit=40)
    still_bookmarked = {post.post_id for post in after.posts if post.bookmarked}
    assert target.post_id not in still_bookmarked
