# Code review

Scope reviewed: `safari_base`, `safari_chat`, `safari_dos`, `safari_fed`, `safari_reader`, `safari_repl`, `safari_slides`, `safari_view`, `safari_writer`.

Skipped by request: `safari_asm` and, assuming `safari_bas` was a typo, `safari_basic`.

Baseline: `make check` passes, so the items below are latent release risks, unimplemented behavior, dead code, or WTF-level logic problems rather than current red-bar failures.

## Findings

### 1. `safari_writer` can silently lose the “final backup before quit”

- Files: `safari_writer\app.py:518-533`
- Problem: `_action_quit()` explicitly says it writes a final backup before showing the quit confirmation, but `write_backup()` is wrapped in `except OSError: pass`.
- Why this matters: if the backup write fails because of permissions, disk full, path issues, etc., the app still proceeds to the “Unsaved changes will be lost. Quit?” prompt with no warning that the promised recovery copy was never created. That is exactly the kind of quiet data-loss path that leads to post-release yanks.

### 2. `safari_chat`’s “conversation tree” is effectively dead code

- Files: `spec\11_ai_chat.md:179-188`, `spec\11_ai_chat.md:670-677`, `safari_chat\state.py:95-115`, `safari_chat\screens.py:381-390`
- Problem: the spec requires a conversation tree, and the UI says it shows branch structure, but `branch_depth` is never actually changed. `add_node()` just copies the previous node’s depth, and `current_branch_id` is defined but never used.
- Why this matters: the feature is presented as implemented, but the stored conversation is flat. Branch-aware UI and state are misleading right now, and any future logic that assumes real branch tracking will be built on a fake foundation.

### 3. `safari_chat` follow-up text leaks state across conversations and app instances

- Files: `safari_chat\engine.py:847-860`, `safari_chat\engine.py:821-822`, `safari_chat\screens.py:237-243`
- Problem: `_pick_followup()` uses a module-global `_FOLLOWUP_COUNTER` instead of conversation state. `/clear` resets the conversation, distress score, and node IDs, but it does not reset that counter.
- Why this matters: the same chat session can produce different follow-up text after a clear, and multiple app instances in the same process will influence each other. That is a classic hidden-global WTF and makes behavior non-deterministic for users and tests.

### 4. `safari_base` raises the wrong exception with a backwards message for directory database paths

- Files: `safari_base\main.py:36-38`
- Problem: when `--database` points at an existing directory, the code raises `NotADirectoryError(f"Not a database file: ...")`.
- Why this matters: the condition is “path is a directory”, but the exception says “not a directory” and the message talks about “not a database file”. This will confuse users immediately when they pass the wrong path and makes error handling harder to trust.

### 5. `safari_fed` silently drops persistence failures for account/cache state

- Files: `safari_fed\app.py:35-39`, `safari_fed\screens.py:535-542`
- Problem: cache writes in `_save_fed_cache()` ignore `OSError`, and screen-level persistence ignores every exception via `except Exception: pass`.
- Why this matters: if saving the active account or cached posts fails, the user gets no signal at all. The next launch can “mysteriously” forget account selection or synced posts, and there is no breadcrumb explaining why.

### 6. `safari_view` still ignores EXIF orientation

- Files: `safari_view\render\pipeline.py:74-86`
- Problem: `_prepare_image()` has an explicit `# TODO: Handle EXIF orientation`.
- Why this matters: photos from phones and cameras often depend on EXIF orientation instead of stored pixel rotation. Those images will display sideways or upside down here, which is a very visible end-user bug in an image viewer.

### 7. `safari_writer` exposes a broken “Index Drive 2” path from the main mail-merge menu

- Files: `safari_writer\screens\mail_merge.py:246`, `safari_writer\screens\mail_merge.py:411-415`, `safari_writer\screens\mail_merge.py:622-651`
- Problem: the main menu advertises “Index Drive 2”, but the `action` path for `index2` just does `self._enter_index(Path.cwd(), "browse")` with a `TODO`, while the keyboard path (`key == "2"`) correctly calls `_enter_index_drive2()`.
- Why this matters: the feature works one way and is broken another way. Users who activate the menu item get the wrong drive browser, while users who press `2` get different behavior. That inconsistency is exactly the sort of thing that slips through if only one interaction path is tested.

### 8. `safari_dos` still presents garbage/restore behavior as if it exists, even though it is explicitly not implemented

- Files: `safari_dos\services.py:45-46`, `safari_dos\services.py:416-425`, `safari_dos\screens.py:1395-1417`, `safari_dos\screens.py:1454`, `spec\09_safari_dos_TODO.md:5-18`
- Problem: the public API keeps `list_garbage()` / `restore_from_garbage()`, but one always returns `[]` and the other always raises. The help text still says “Garbage restores items without permanent delete”, while the actual garbage screen tells users to use the OS file manager because restore is not supported.
- Why this matters: this is half-implemented, contradictory behavior. The screen, help text, API surface, and spec TODO are not aligned, so users and downstream callers get a misleading picture of what Safari DOS can actually do.
