# Safari Fed

Safari Fed is a calm, keyboard-driven Mastodon client built into the Safari suite. It treats the fediverse like a retro message system — more Pine or BBS reader than infinite-scroll social app.

## Starting Safari Fed

```bash
safari-fed
```

Optional flags:

- `--folder HOME|Mentions|Bookmarks|Drafts|Sent|Deferred` — open a specific folder on launch.
- `--account NAME` — start with a configured Mastodon identity selected.

If no Mastodon credentials are configured, Safari Fed opens in demo mode with a seeded local packet so you can explore the interface.

## Connecting to Mastodon

Copy `.env.example` to `.env` and fill in your credentials.

**Single account (legacy pattern):**
```
MASTODON_BASE_URL=https://mastodon.social
MASTODON_ACCESS_TOKEN=your_access_token_here
```

**Multiple accounts:**
```
MASTODON_ID_MAIN_BASE_URL=https://mastodon.social
MASTODON_ID_MAIN_ACCESS_TOKEN=your_main_access_token
MASTODON_ID_ART_BASE_URL=https://mastodon.art
MASTODON_ID_ART_ACCESS_TOKEN=your_art_access_token
MASTODON_DEFAULT_ID=MAIN
```

## Folders

Safari Fed organises posts into folders like a mail program:

- **Home** — your main timeline.
- **Mentions** — posts that mention you.
- **Bookmarks** — posts you have bookmarked.
- **Drafts** — locally saved compose drafts.
- **Sent** — posts you have sent this session.
- **Deferred** — posts you have pushed aside for later.

## Navigation

- **J / Down** — move to the next post.
- **K / Up** — move to the previous post.
- **PageDown / PageUp** — skip 5 posts at a time.
- **Enter** — open the reader view for the selected post.
- **T** — open the thread tree view.
- **Esc / Q** — return to the index or quit.

## Folder Navigation

- **Tab / Shift+Tab** — cycle through folders.
- **H** — jump to Home.
- **N** — jump to Mentions.
- **G** — advance to the next folder.

## Post Actions

- **C** — compose a new post.
- **R** — reply to the selected post.
- **B** — boost the selected post.
- **F** — favourite the selected post.
- **M** — toggle bookmark on the selected post.
- **X** — toggle the post between read and unread.
- **D** — defer the post to the Deferred folder.
- **U** — sync from Mastodon (requires credentials).
- **W** — export the selected post or thread to Safari Writer.
- **~** — run a Safari BASIC macro against the current post and save the output as a draft.

## Compose

Press **C** to open the built-in compose editor or **R** to start a reply.

- **Ctrl+X** — send the post.
- **Ctrl+S** — save as a local draft.
- **Esc** — cancel without saving.

When running inside the full Safari Writer app, **C** and **R** open the full Safari Writer editor instead of the mini compose shell.

## Multi-Account Support

- **A** — cycle through configured accounts.
- **1–9** — select an account by its position in the account bar.

Each account keeps its own folder state, compose buffer, and sync status.

## Writing Handoff

Press **W** on any post or thread to export it as plain text and open it in Safari Writer for editing, quoting, or drafting a blog post. In thread view, the full thread tree is exported.

## Help

- **F1 / ?** — display the full key-command reference.
- **Ctrl+Q** — quit Safari Fed immediately from any view.
