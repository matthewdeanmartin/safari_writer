# safari_fed integration tests (mastodon_mock-backed)

`test_fed_against_mock.py` runs `safari_fed`'s real Mastodon client
(`SafariFedClient`) against [`mastodon_mock`](../../mastodon_mock) — an
unpublished, stateful mock Mastodon server — booted as a local HTTP server. **No
live instance, no API keys.**

safari_fed is a retro TUI Mastodon client with both read and write features.
Because the mock is local-only and stateful, the **write** surface (post, reply,
favourite, reblog, bookmark) is safe to exercise here — nothing ever leaves
localhost — which is the whole point of using the mock instead of a live server.

## What they prove

- **Read**: `fetch_sync_result` aggregates home + bookmarks + notifications into
  normalized `FedPost`s; tags render; `@mentions` are flagged; boosts render with
  a "Boosted by @…" prefix.
- **Write** (against the localhost mock): `send_post` round-trips into the
  timeline; replies thread and carry visibility; spoiler/CW text renders;
  `favourite`/`reblog` succeed; `bookmark` → appears in sync → `unbookmark`
  removes it.
- Direct/private posts get the `private` flag and `direct=True`.

## How it works

The module boots `mastodon_mock` (module-scoped, in-memory, seeded with `me`
following `friend`) and builds a `SafariFedClient` from a `MastodonIdentity`
pointed at it — no env-var juggling. A second `friend` client sets up state
(mentions, posts to boost/bookmark) that the `me` client then reads.

## Running

```bash
uv run pytest test_integration/test_fed_against_mock.py
# or
make test-fed-integration
```

Self-skips on Python < 3.13 or if `mastodon_mock` is not installed (it is an
editable path dev dependency on the sibling repo; see `[tool.uv.sources]` in
`pyproject.toml`). Drop that path source for a version pin once `mastodon_mock`
is published.

## Findings

Driving safari_fed against the mock surfaced **no mock bugs** — the mock served
every surface safari_fed touches (verify_credentials, home/bookmarks/
notifications, status_post with reply/visibility/spoiler, favourite/reblog/
bookmark/unbookmark, media upload + attachment rendering) faithfully. See the
mock repo's `spec/findings_from_safari_fed.md`.
