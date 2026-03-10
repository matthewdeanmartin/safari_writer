# Learnings 03: Textual Widget Scrolling Does Not Work With render()

This note is for future clankers working on any custom Textual widget that
needs to scroll its content.

## The trap

You write a custom `Widget` subclass. You override `render()` to return a big
multi-line string. You set `overflow-y: auto` in CSS. You override
`get_content_height()` to return the true content height. You call
`self.scroll_to(y=...)` to move the viewport.

**None of this works.** The viewport never moves. The content below the fold
is simply invisible and unreachable.

## Why it doesn't work

Textual's `Widget.render()` produces a static renderable that is **clipped to
the widget's allocated size**. There is no virtual-scroll layer between
`render()` and the screen.

- `overflow-y: auto` adds a scrollbar *gutter* but the scroll machinery has
  nothing to scroll because `virtual_size` is never set larger than the
  widget's actual size.
- `get_content_height()` is only called when the widget has `height: auto` in
  CSS. If you use `height: 1fr` (or any explicit/fractional height), Textual
  never calls it. It is dead code.
- `scroll_to()` clamps to `max_scroll_y`, which equals
  `virtual_size.height - container_size.height`. Since `virtual_size` equals
  the widget size, `max_scroll_y` is always 0. Every scroll request is
  clamped to zero.
- Manually setting `self.virtual_size = Size(w, big_number)` does not help
  because `render()` still produces a single block that is clipped, not
  virtually scrolled.

## The two approaches that actually work

### 1. Manual viewport slicing (what Safari Writer uses)

Keep a `_scroll_offset: int` on your widget. In `render()`, only emit the
lines from `buffer[_scroll_offset : _scroll_offset + visible_height]`. On
every cursor move, adjust `_scroll_offset` so the cursor row stays in the
visible window. This is the same technique used by the ANSI preview screen
(`PrintPreviewScreen` in `screens/print_screen.py`).

Advantages:
- No base-class change required; stays a plain `Widget`.
- Simple to understand and debug.
- Performance win: only visible lines are rendered.

Disadvantage:
- You manage scroll state yourself (trivial in practice).

### 2. Inherit from ScrollView and use render_line()

Textual's `ScrollView` base class supports true virtual scrolling. Instead of
`render()`, you implement `render_line(y: int) -> Strip` which is called only
for visible lines. You must also keep `self.virtual_size` up to date whenever
the content changes.

This is how Textual's own `TextArea`, `RichLog`, `DataTable`, and `Tree`
widgets work internally. It is the "official" approach but requires a larger
refactor if you already have a `render()` implementation.

### 3. Wrapping in VerticalScroll (container-level scrolling)

Put your widget inside a `VerticalScroll` container and give the widget
`height: auto` CSS so it expands to its full content height. The container
handles scrolling. This is the simplest option but renders the entire content
every frame, which is slow for large buffers.

## How to detect you've fallen into the trap

If you see any of these in a custom widget, the scroll is probably broken:

- `overflow-y: auto` combined with `height: 1fr` or any non-auto height
- `get_content_height()` override on a non-auto-height widget
- `scroll_to()` calls wrapped in `try/except` that silently swallow errors
- `call_after_refresh()` used to defer scroll calls (a sign the timing is wrong)

## History

This bug was present from the initial editor implementation. The cursor could
be moved past the bottom of the screen with arrow keys or typing, but the
viewport never followed. It was fixed by adopting manual viewport slicing
(approach 1) in `EditorArea._scroll_to_cursor()` and `EditorArea.render()`.

Fixed by Claude Code (Claude Opus 4.6), March 2026.
