# Safari-Mastodon Concept

AtariWriter is the text editor, but Pine is the general UI.

## Working names

* Safari-Fed

## Core idea

A Mastodon client designed as though a very capable late-1980s text-mode communications and mail program had been given access to the fediverse. The interface should feel closer to **Pine**, **Elm**, terminal BBS readers, and 8-bit-era menu software than to a modern social app. The goal is not infinite scroll addiction. The goal is calm, deliberate reading and posting.

Because modern email volume is overwhelming, Mastodon is a better fit for this style: messages are short, threadable, and can be processed in batches.

## Design pillars

### 1. Calm batch processing

The user should review posts in a queue-like way rather than falling into endless scrolling.

### 2. Keyboard first

Everything should be reachable by one keystroke or a short command.

### 3. Retro but useful

It should feel old-school without recreating old limitations that made software miserable.

### 4. Readable over flashy

Favor dense text summaries, thread views, author cards, and compact navigation.

### 5. Local-first resilience

Cache aggressively so the app feels like an offline reader that syncs when needed.

## Historical feel to borrow

### Pine influence

From Pine, borrow:

* the top title bar
* index pane of messages/posts
* single-keystroke commands shown in a footer
* deliberate navigation between list view and message view
* status messages like "3 posts selected" or "Reply queued"

### 8-bit Atari / telecom influence

For an Atari-adjacent feel, borrow from:

* terminal programs and BBS message readers
* disk utility style menus
* inverse-video selection bars
* strong screen framing with headers and footers
* function-key legends and control-key shortcuts

This should feel like **a communications program**, not a website.

## Main screens

## 1. Home / timeline index

This is the default screen.

It should resemble a mail index or forum message list.

Example layout:

```text
+----------------------------------------------------------------------------+
| SAFARI-TOOT  Home Timeline                                  124 unread     |
+----------------------------------------------------------------------------+
| #  F  Author           Age   Boosts Fav  Preview                            |
|----------------------------------------------------------------------------|
| 1  *  @alice           2m    14     22   Python packaging is weird again... |
| 2     @bob             5m    2      11   Anyone know an AtariWriter clone?  |
| 3  !  @carol           9m    8      30   Long thread: static site generation |
| 4     @dan             14m   0      3    New blog post on Mastodon clients   |
| 5  @  @erin            17m   1      6    You were mentioned in a thread      |
|----------------------------------------------------------------------------|
| J/K Move  Enter View  R Reply  B Boost  F Fav  C Compose  / Search  G Goto |
+----------------------------------------------------------------------------+
```

Flags:

* `*` unread
* `!` bookmarked or important
* `@` mention
* `D` direct/private visibility post
* `T` thread starter

## 2. Post reader view

Opens one post and shows context.

```text
+----------------------------------------------------------------------------+
| Post 2 of 124                                         Thread depth: 3       |
+----------------------------------------------------------------------------+
| Author:   @bob@example.social                                           |
| Posted:   2026-03-08 15:20                                              |
| CW:       none                                                           |
| Tags:     #retcomputing #python                                          |
|-------------------------------------------------------------------------|
| Anyone know an AtariWriter clone? I want the menus and keybindings,     |
| not just a generic text editor in curses.                               |
|                                                                         |
| [1 attachment omitted]                                                  |
|-------------------------------------------------------------------------|
| Replies: 12   Boosts: 2   Favourites: 11                                |
|-------------------------------------------------------------------------|
| P Prev  N Next  T Thread  A Author  R Reply  B Boost  F Fav  S Save     |
+----------------------------------------------------------------------------+
```

## 3. Thread view

This is one of the most important screens.

The thread should look like a message tree or forum reader, not like a chat app.

```text
Thread: AtariWriter clone discussion

> @bob
  Anyone know an AtariWriter clone?

>> @matthew
   I want one with real menu vibes.

>>> @carol
    You might want to emulate Pine-style indexes too.

>> @dan
   There was an old attempt, but it missed the keybindings.
```

Thread features:

* collapse/expand branches
* jump to parent
* jump to next unread reply
* save full thread as text or markdown

## 4. Compose screen

Compose should feel like a tiny mail editor.

```text
+----------------------------------------------------------------------------+
| Compose Post                                                               |
+----------------------------------------------------------------------------+
| Visibility: Public   CW: none   Attachments: 0                            |
| Replying to: @bob                                                         |
|----------------------------------------------------------------------------|
| I would absolutely use a retro TUI Mastodon client if it had a proper     |
| thread viewer and a queue-based reading mode.                             |
|                                                                            |
|----------------------------------------------------------------------------|
| ^X Send  ^S Save Draft  ^T CW  ^V Visibility  ^A Attach  ^C Cancel        |
+----------------------------------------------------------------------------+
```

The editor can be line-oriented or full-screen, depending on what the Safari suite already uses.

## 5. Notifications / mentions

This should feel like an inbox.

Categories:

* Mentions
* Replies
* Follows
* Favourites
* Boosts
* Admin/system notices

A user should be able to triage notifications quickly.

## 6. Saved / bookmarked posts

A reading-later shelf.

Useful because retro clients benefit from intentional workflows:

* bookmark now
* read later
* export thread
* add to notes

## 7. Author profile screen

This should feel like viewing a sender card in an email client or BBS user profile.

Show:

* display name
* handle
* bio
* follower/following counts
* recent posts index
* mute/block/follow actions

## 8. Search / local archive

Very useful in a retro productivity app.

Allow:

* search cached posts
* search authors
* search tags
* search your own posts
* search bookmarks

The search UX should resemble searching message folders.

## Special modes

## Queue mode

This is the killer feature.

Instead of infinite scrolling, the app maintains a processing queue:

* unread home posts
* unread mentions
* unread bookmarks
* saved searches

The user works through posts like email.

Commands:

* mark read
* defer
* bookmark
* reply
* mute author
* open thread
* archive locally

This makes Mastodon manageable and gives the app a real reason to exist.

## Digest mode

Generate condensed summaries of the timeline by author or topic.

Examples:

* "Top 20 unread posts"
* "Posts mentioning Python"
* "Threads with 5+ replies"
* "Posts from people I follow closely"

This could be a plain-text digest screen, almost like a bulletin summary.

## Slow-feed mode

Optional setting that deliberately limits sync frequency and number of new posts shown at once.

Examples:

* fetch at most 40 new posts per sync
* emphasize meaningful threads over volume
* hide boosts unless explicitly requested

This would suit the retro ethos very well.

## Suggested command set

Pine-style footer commands are essential.

Global:

* `?` help
* `Q` quit
* `G` go to folder/view
* `/` search
* `C` compose
* `U` sync/fetch updates
* `L` refresh local cache index
* `O` options

Index view:

* `J` / `K` move
* `Enter` open
* `R` reply
* `B` boost
* `F` favourite
* `M` bookmark
* `T` view thread
* `A` author profile
* `D` defer
* `X` mark read

Reader view:

* `N` next
* `P` previous
* `T` thread
* `H` home timeline
* `S` save/export
* `W` open in browser

Thread view:

* `[` parent
* `]` next sibling
* `+` expand
* `-` collapse
* `R` reply to selected post

## Folder / mailbox metaphor

Instead of calling everything a timeline, present them like folders or message areas:

* Home
* Local
* Federated
* Mentions
* Bookmarks
* Drafts
* Sent
* Saved Searches
* Hidden / Deferred

This is a strong Pine callback and makes the app feel purposeful.

## Visual style

### Preferred look

* monochrome or 4-color palette themes
* inverse highlight bar
* ASCII/box-drawing borders
* dense text rows
* no emojis rendered as giant distractions unless opened explicitly

### Theme options

* Green Screen
* Amber Terminal
* Blue Atari Office
* White on Blue DOS-ish
* Dark BBS

### Typography behavior

In a terminal/TUI context, treat typography as spacing discipline:

* fixed-width only
* align columns carefully
* wrap long posts with indentation
* optionally transliterate fancy Unicode for compatibility mode

## Media handling

Keep media minimal and optional.

Options:

* show `[IMG]`, `[VID]`, `[POLL]`, `[LINK]`
* open media in external browser/viewer
* optionally render alt text inline
* never force heavy previews into the main list

This keeps the client fast and true to the text-first concept.

## Practical modern features

To make it genuinely useful, include a few non-1980s capabilities under the hood:

* robust local cache with SQLite
* draft autosave
* offline reading of cached posts and threads
* configurable filters and mutes
* export threads to Markdown
* search over cached content
* optional LLM-generated digest summaries
* multiple-account support

But these should be surfaced in a retro-feeling way.

## Integration with the Safari suite

This concept becomes stronger if it plugs into your other modules.

### With Safari-Writer

* send selected post/thread to Writer as a text document
* create quote collections
* write blog drafts based on saved posts

### With Safari-Base

* maintain local contacts / favorite authors / tag lists
* store curated thread metadata

### With Safari-Chat

* help system that explains Mastodon concepts in a gentle Eliza-like way
* maybe a "why is my feed weird" assistant

### With Safari-DOS

* local archive folders
* import/export
* safe trash behavior for saved items and drafts

### With Safari-BASIC

* macros such as:

  * export all bookmarked posts tagged #python
  * batch mute certain regexes
  * create a digest for one account

## Strong feature ideas with 8-bit callback energy

### 1. Message packet mode

A nod to offline readers and BBS packets.

The app can fetch a batch of posts into a local packet:

* read offline
* reply offline
* sync later

### 2. Sysop-style account status screen

Show sync status, cache size, last fetch, API rate limit, drafts pending.

### 3. Bulletin board mode

Show trending or curated posts as if they were bulletin items.

### 4. Signature blocks

Very email-like and period-appropriate.

### 5. Tag conferences

Treat hashtags like message conferences or forums.

Examples:

* `#python`
* `#retcomputing`
* `#fairfax`

## Why this works better than retro email

Mastodon is a better fit than email because:

* posts are shorter
* conversation trees are public and easier to browse
* triage can be done in batches
* social discovery works better with a list/index UI
* a local archive is genuinely useful

Email today is too high-volume and heterogeneous. Mastodon can still plausibly be handled like a message board or mailbox.

## Minimal viable product

If you wanted a first version, I would build:

1. Home timeline index
2. Post reader
3. Thread view
4. Compose/reply
5. Mentions inbox
6. Bookmarks
7. Local cache/search
8. Queue mode

That is enough to make the product feel real.

## Best one-sentence pitch

**Safari-Toot is a calm, keyboard-driven Mastodon client that treats the fediverse like a high-quality retro message system instead of an infinite-scroll website.**

## Positioning

* retro interface
* modern usefulness
* lower-stress social reading
* better thread handling
* local-first archive
