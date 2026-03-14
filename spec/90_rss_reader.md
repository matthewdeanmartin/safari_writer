# Spec: Safari Feed

## Purpose

Add Safari Feed, a terminal-first RSS/Atom reader that feels like the rest of Safari Writer: menu-driven, keyboard-first, pane-based, and calm. The user points the app at OPML files in `~/.config/safari_writer/`, browses those OPML files, browses feeds within a selected OPML file, fetches a feed, and reads items in a text pane inside the terminal.

This is a spec only. No implementation is described here beyond product-level behavior and architectural guidance.

## Core user story

1. User launches Safari Feed from the Safari Writer main menu.
1. User sees a list of OPML files from `~/.config/safari_writer/*.opml`.
1. User opens one OPML file and sees its feeds.
1. User selects a feed and chooses `Fetch`.
1. User sees feed items in an index pane and article content in a reading pane.
1. User can toggle the content source between:
   - what was present in the RSS/Atom entry itself
   - what was fetched from the linked article URL
1. User can choose HTML-to-Markdown or HTML-to-ANSI rendering.
1. Read/unread state persists in the config folder.

## Design goals

- Match Safari Writer / Safari Reader interaction patterns rather than inventing a new shell.
- Make feed reading feel like a utility or inbox, not a browser tab.
- Prefer structured lists, stable headers, and visible footer commands.
- Keep article reading entirely text-first.
- Never execute JavaScript.
- Make fetched-page reading optional and explicit, not automatic magic.

## Non-goals

- Not a full web browser.
- Not an Electron-style RSS app.
- Not a sync service.
- Not a social reader with comments, likes, or sharing.
- Not a JS-capable DOM runtime.

## Input and discovery

### OPML source

The app scans:

- `~/.config/safari_writer/*.opml`

Behavior:

- Zero OPML files is valid and should show an empty-state screen with a short hint.
- Multiple OPML files are listed by filename.
- OPML files are read-only from this app in v1.
- Nested outlines should be preserved as feed groups where possible.

### Feed types

Required:

- RSS 2.0
- Atom

Nice to have later:

- RDF variants

## Main screen model

The reader should use the same basic structure already seen elsewhere in the repo:

- top status/header bar
- central work area
- bottom footer with key hints

Preferred primary flow:

1. OPML Library Screen
1. Feed List Screen
1. Feed Reader Screen
1. Article Reader Screen or split-pane Feed Reader mode

The implementation may make the feed/item/article experience one screen with panes or a pair of adjacent screens, but it should still feel like one coherent reader.

## Screen 1: OPML Library

Purpose:

- show detected OPML files
- show file count and last refresh time
- allow opening one OPML file

Columns:

- filename
- modified time
- feed count if cheaply available

Footer commands:

- `Enter=Open`
- `R=Rescan`
- `Q=Back`
- `H=Help`

Empty state:

- `No OPML files found in ~/.config/safari_writer`
- short hint that the app watches `*.opml` there

## Screen 2: Feed List

Purpose:

- show all feeds from the chosen OPML file
- preserve folder/group labels from OPML where possible
- let the user fetch one feed

Columns:

- group
- feed title
- site/domain
- unread count
- last fetched

Footer commands:

- `Enter=Open Feed`
- `F=Fetch`
- `A=Fetch All In This OPML`
- `R=Refresh List`
- `Q=Back`

Notes:

- Fetching should be explicit.
- The user should not need to leave the keyboard flow to update a feed.

## Screen 3: Feed Reader

Purpose:

- browse items in one feed
- preview selected item metadata
- open article content in the reading pane

Preferred layout:

- left pane: item index
- right pane: article text
- top line: feed title, fetch time, mode indicators
- bottom line: command legend

Item row fields:

- unread/read marker
- publication date/time
- item title
- optional author

Status indicators:

- current feed name
- current item position
- content mode: `FEED` or `FETCHED`
- render mode: `MD` or `ANSI`
- fetch status: `ONLINE`, `OFFLINE`, `ERROR`, or `CACHED`

Footer commands:

- `Up/Down=Move`
- `Enter=Read`
- `M=Mark Read/Unread`
- `F=Fetch Feed`
- `O=Fetch Article`
- `T=Toggle Feed/Fetched`
- `V=Toggle Markdown/ANSI`
- `Q=Back`

## Screen 4: Article Reader

If a dedicated full-screen article view is used, it should resemble the existing print preview and output screens:

- full-screen read-only text
- stable header with title and line/page status
- keyboard scrolling with `Up/Down`, `PgUp/PgDn`, `Home/End`
- `T` to toggle content source
- `V` to toggle render style
- `M` to mark read/unread
- `Q` or `Esc` to return

If the article stays in a split pane, these same commands should still exist.

## Content modes

Each item has two text sources:

### 1. Feed content

Derived only from the feed entry:

- title
- summary/description/content fields
- author/date metadata
- enclosure metadata as text labels only

This mode is always available when the feed contains body text.

### 2. Fetched content

Derived from a direct HTTP fetch of the item URL.

Rules:

- fetch only on explicit user action or when toggling into fetched mode and no cached fetch exists
- no JavaScript execution
- no headless browser
- ignore dynamic content that requires JS
- store fetched text locally for later rereading
- preserve the original URL and fetch timestamp

If fetching fails, the app should keep the user in feed-content mode and show a short status message.

## Rendering modes

The user can choose per session, and optionally persist a default:

### Markdown mode

Pipeline:

- feed HTML or fetched HTML
- sanitize
- convert to Markdown-ish plain text
- display as readable terminal text

Goal:

- best for export, copying, and consistent wrapping

### ANSI mode

Pipeline:

- feed HTML or fetched HTML
- sanitize
- convert directly into terminal-friendly styled text
- limited emphasis only: headings, links, lists, block quotes, code, bold/italic where practical

Goal:

- richer terminal reading while staying text-first

The conversion backend is an implementation detail, but the user-facing choice is simple:

- `Markdown`
- `ANSI`

## HTML handling constraints

- No JavaScript.
- Strip `script`, `style`, `noscript`, and tracking cruft.
- Resolve relative links using the article URL when needed.
- Prefer readable article text over full-page chrome.
- Preserve headings, paragraphs, lists, code blocks, and quotes when possible.
- Links should remain visible as text, not hidden behind mouse-only affordances.

## Read/unread state

Persist state under the config folder, not in the project workspace and not in a surprise home subdirectory.

Suggested files:

- `~/.config/safari_writer/safari_feed_state.json`
- `~/.config/safari_writer/safari_feed_cache/`

Persist at minimum:

- known OPML files
- feed URL
- item GUID or stable fallback key
- read/unread flag
- starred or saved flag if added later
- last fetched timestamp per feed
- cached fetched article text
- chosen content source for the current item if useful
- preferred render mode

Stable item identity should prefer:

1. item GUID / Atom id
1. permalink URL
1. title + published timestamp hash

## Caching and fetch behavior

- Feed fetches should cache raw response text and parsed item metadata.
- Article fetches should cache sanitized source plus rendered text artifacts if useful.
- Re-fetch should be explicit and visible.
- The UI should distinguish:
  - never fetched
  - fetched successfully
  - fetch failed
  - cached only

## Error handling

Use short, old-school utility wording consistent with the rest of the suite.

Examples:

- `NO OPML FILES FOUND`
- `FEED FETCH FAILED`
- `ARTICLE FETCH FAILED`
- `NO FEED BODY AVAILABLE`
- `NO FETCHED ARTICLE CACHED`
- `READ STATE COULD NOT BE SAVED`

Do not drop tracebacks into the main UI.

## Commands and key model

Global expectations:

- `Esc` or `Q` backs out
- arrow keys move selection
- `Enter` activates current selection
- footer always shows the important keys

Reader-specific commands:

- `F` fetch current feed
- `O` fetch current article URL
- `T` toggle `FEED` / `FETCHED`
- `V` toggle `Markdown` / `ANSI`
- `M` mark read/unread
- `N` next unread item
- `P` previous unread item
- `R` refresh or rescan, depending on screen
- `H` help

## Suggested user flow details

### First run

1. User opens Safari Feed.
1. App scans `~/.config/safari_writer/*.opml`.
1. If no files exist, show empty state and quit/help options.
1. If files exist, focus the first OPML file.

### Reading a feed

1. Open an OPML file.
1. Select a feed.
1. Press `F` to fetch.
1. Browse items with arrow keys.
1. Read the selected item in the text pane.
1. Press `T` to compare feed-body text with fetched-article text.
1. Press `V` to switch rendering style.
1. Mark items read as you go.

## Acceptance criteria

The feature is acceptable when:

1. The app can list zero or more OPML files from `~/.config/safari_writer/*.opml`.
1. The user can open an OPML file and browse feeds.
1. The user can fetch a feed on demand.
1. The user can browse feed items in a list and read article text in-terminal.
1. The user can switch between feed-provided content and fetched-page content.
1. The user can switch between Markdown-style and ANSI-style rendering.
1. No JavaScript engine is involved.
1. Read/unread state survives app restarts and is stored in `~/.config/safari_writer/`.

## Pointers for the next clanker

Do not start from a blank slate. Read these first and steal the patterns:

- `safari_reader/screens.py`
  - Existing menu screen, library screen, reader screen, help screen, and settings patterns.
  - Reuse its header/footer rhythm, `Binding` style, and list-driven navigation.
- `safari_reader/state.py`
  - Baseline for a shared state object across screens.
  - Extend this style for OPML/feed/item/article state rather than passing ad hoc dicts everywhere.
- `safari_reader/services.py`
  - Existing service split for loading, parsing, persistence, and network fetch behavior.
  - Mirror this separation for OPML parsing, feed fetch, article fetch, and cache/read-state persistence.
- `safari_writer/screens/output_screen.py`
  - Good minimal full-screen read-only text viewer.
  - Useful if article reading becomes a dedicated full-screen screen.
- `safari_writer/screens/print_screen.py`
  - The print preview already solves scrollable, full-screen, read-only terminal text with a status header.
  - Its rendering split is a good mental model for `Markdown` vs `ANSI`.
- `safari_writer/app.py`
  - See how Safari Writer enters and exits sub-apps like `safari_reader`.
  - Follow the existing handoff pattern instead of adding custom top-level plumbing.

Pattern guidance:

- Keep stateful data in a dedicated state object.
- Keep network/disk/parsing logic in services.
- Keep screens thin and command-oriented.
- Use simple modal or full-screen transitions, not lots of tiny widgets fighting each other.
- Preserve the suite’s visible footer-command culture.

## Suggested implementation shape

This is not a requirement, but it would fit the repo well:

```text
safari_rss/
  __init__.py
  app.py
  state.py
  services.py
  screens.py
  models.py
```

Or, if this is treated as an extension of `safari_reader`, keep the same separation internally.

## One-sentence vision

Safari Feed should feel like a retro terminal inbox for feeds: OPML in, articles out, keyboard all the way down.
