# Learnings: Textual Key Handling on Windows Terminal

## Problem: Ctrl+V paste didn't work

### Root cause

On Windows Terminal (and mintty/Git Bash), pressing Ctrl+V triggers the terminal's built-in paste behavior. The terminal intercepts the keystroke, reads the system clipboard, and sends the clipboard content to the application wrapped in **bracketed paste escape sequences** (`\e[200~`...`\e[201~`).

Textual parses this as an `events.Paste` event — **not** a `events.Key` event. This means:

- `on_key` never sees `key == "ctrl+v"`
- `Binding("ctrl+v", ...)` never fires
- Only `on_paste(self, event: events.Paste)` receives the event

### Additional complication: terminal paste text is garbage

The `event.text` in the Paste event contains whatever is on the **system clipboard**, not the app's internal clipboard. In our case it was the terminal window title "Git Bash". This must be ignored.

### Why Ctrl+X and Ctrl+C worked differently

- **Ctrl+X** (`\x18`): The terminal does not intercept this. It arrives as a normal Key event and the `Binding("ctrl+x", "editor_cut", priority=True)` fires correctly.
- **Ctrl+C** (`\x03`): Textual has a built-in system binding `Binding("ctrl+c", "help_quit", system=True)`. We override it with `priority=True` on the widget, so our copy action fires instead.

### Solution

1. **BINDINGS with `priority=True`** on `EditorArea` for `ctrl+c`, `ctrl+v`, `ctrl+x`. This overrides Textual's system `ctrl+c` binding and provides action methods for cut/copy/paste.

1. **`on_paste` handler** that:

   - Catches the terminal's bracketed paste event (which is what Ctrl+V actually produces)
   - **Ignores** `event.text` (the system clipboard / terminal junk)
   - Calls `_paste()` to insert from the **internal** app clipboard
   - Calls `event.stop()` to prevent further propagation

### Key rule for future development

> In a Textual TUI on Windows Terminal, **Ctrl+V will never arrive as a Key event**. Always handle it via `on_paste`. Do not trust `event.text` from paste events if using an internal clipboard.

### Code pattern

```python
class EditorArea(Widget, can_focus=True):
    from textual.binding import Binding

    BINDINGS = [
        Binding("ctrl+c", "editor_copy", "Copy", show=False, priority=True),
        Binding("ctrl+v", "editor_paste", "Paste", show=False, priority=True),
        Binding("ctrl+x", "editor_cut", "Cut", show=False, priority=True),
    ]

    def on_paste(self, event: events.Paste) -> None:
        """Ctrl+V arrives as Paste, not Key. Ignore terminal text, use internal clipboard."""
        event.stop()
        self._paste()  # uses self.state.clipboard (internal)
        self.refresh()

    def action_editor_copy(self) -> None:
        self._copy()
        self.refresh()

    # ... etc
```

The Ctrl+V binding is kept in BINDINGS as a fallback for terminals that don't use bracketed paste, but on Windows Terminal, `on_paste` is what actually fires.
