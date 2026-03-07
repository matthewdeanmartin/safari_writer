# Safari Writer - Bugs & Issues

All bugs marked FIXED have been resolved in this commit.

---

## BUG-01: Test helpers missing `_heading_active` and `_chain_active` attributes
**Files:** `tests/test_editor.py`, `tests/test_search_replace.py`, `tests/test_selection.py`
**Severity:** Low
**Details:** `EditorArea.__init__` sets `_heading_active` and `_chain_active`, but the test helpers that bypass `__init__` don't set them. Any test touching prompt-mode key dispatch would crash.
**Status:** FIXED - Added missing attributes to all `make_editor()` helpers.

## BUG-02: Backspace at document start falsely sets `modified = True`
**File:** `safari_writer/screens/editor.py` `_backspace()`
**Severity:** Medium
**Details:** `_backspace()` unconditionally sets `s.modified = True` even when cursor is at (0,0) and nothing changes.
**Status:** FIXED - Only set modified when an actual deletion occurs.

## BUG-03: Delete at end of last line falsely sets `modified = True`
**File:** `safari_writer/screens/editor.py` `_delete_char()`
**Severity:** Medium
**Details:** Same as BUG-02 but for `_delete_char()`.
**Status:** FIXED - Only set modified when an actual deletion occurs.

## BUG-04: Word wrap cursor column can go negative
**File:** `safari_writer/screens/editor.py` `_apply_word_wrap()`
**Severity:** Medium
**Details:** The cursor reposition formula after wrapping could produce a negative column if the stripped whitespace count exceeds expectations.
**Status:** FIXED - Clamped result with `max(0, ...)`.

## BUG-05: `schema_matches` only compares `max_len`, not field names
**Status:** Not a bug - by design (matches original AtariWriter behavior).

## BUG-06: Menu "F" key binding had mismatched action and label
**Files:** `safari_writer/screens/main_menu.py`, `safari_writer/app.py`
**Severity:** Medium
**Details:** The binding action and menu label were mismatched.
**Status:** FIXED - Aligned binding, menu item, and handler to `new_folder`. Shows "not yet implemented".

## BUG-07: `GlobalFormat.reset_defaults()` uses fragile `self.__init__()`
**File:** `safari_writer/state.py`
**Severity:** Low
**Details:** Calling `__init__()` on a dataclass to reset is an anti-pattern.
**Status:** FIXED - Uses proper field-by-field reset from a fresh `GlobalFormat()` instance.

## BUG-08: Search wrap-around can find same match infinitely
**Status:** Not a bug - wrap-around search is correct behavior per spec.

## BUG-09: `?` key opens help instead of inserting `?` character
**File:** `safari_writer/screens/editor.py` `on_key()`
**Severity:** High
**Details:** `question_mark` was in the help trigger list, intercepting `?` before the printable character handler. Users could never type `?` in the editor.
**Status:** FIXED - Removed `question_mark` from help trigger. F1 is sufficient.

## BUG-10: Rich markup in document text is interpreted instead of displayed
**File:** `safari_writer/screens/editor.py` `_render_line()`
**Severity:** High
**Details:** Typing `[bold]` or `[red]` in document text would be interpreted as Rich markup. Square brackets need escaping.
**Status:** FIXED - `[` characters in regular text are escaped as `\[` before rendering.

## BUG-11: `Ctrl+M` may be unreachable (terminal maps it to Enter)
**File:** `safari_writer/screens/editor.py`
**Severity:** Medium (terminal-dependent)
**Details:** In many terminals `Ctrl+M` and `Enter` produce identical key codes (`\r`). Textual may not distinguish them, making the paragraph mark shortcut unreachable.
**Status:** Known limitation - documented. Use the editor's Ctrl+M binding; if your terminal doesn't distinguish it, paragraph marks can still be inserted via other means.

## BUG-12: `_delete_to_eof` edge case
**Status:** Not a bug - buffer correctly contains `[""]` after full deletion.

## BUG-13: File operations (Load, Save, Delete) were unimplemented stubs
**Files:** `safari_writer/app.py`, new `safari_writer/screens/file_ops.py`
**Severity:** Feature gap
**Status:** FIXED - Implemented Load, Save, and Delete file operations with filename prompt modal.

## BUG-14: Word wrap may produce double spaces when merging with next line
**File:** `safari_writer/screens/editor.py` `_apply_word_wrap()`
**Severity:** Low
**Details:** The space insertion between wrapped tail and existing next line doesn't check for existing spaces.
**Status:** Accepted - behavior is consistent with original AtariWriter word wrap.

## BUG-15: Tab in type-over mode
**Status:** Not a bug - tab is navigation, not character insertion, in type-over mode.

## BUG-16: `MainMenuScreen` missing `set_message` method
**File:** `safari_writer/screens/main_menu.py`
**Severity:** Medium
**Details:** `app.set_message()` silently dropped messages on the main menu because the screen had no `set_message` method. "Not yet implemented" messages were invisible.
**Status:** FIXED - Added `set_message()` to `MainMenuScreen` (displays in status bar).

## BUG-17: Caps Lock mode had no keyboard toggle
**File:** `safari_writer/screens/editor.py`
**Severity:** Low (feature gap)
**Details:** The `caps_mode` state existed but had no key binding to toggle it.
**Status:** FIXED - Added `caps_lock` key binding and updated help text.
