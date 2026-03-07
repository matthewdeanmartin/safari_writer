## Project Vibe

Safari Writer is a Textual TUI application that clones AtariWriter. The aesthetic is retro, classic, CLI-first. We
value:

- Clean, readable code over clever tricks
- Consistency with existing patterns
- Working code over premature abstraction

## Development Environment

```bash
# Install dependencies
make install

# Run in dev mode (auto-reload)
make dev

# Run normally
make run
```

All commands use `uv` — **never use bare `python` or `pip`**.

## Code Style

### Docstrings: Google Style

All public functions, classes, and modules need Google-style docstrings.

```python
def load_document_buffer(path: Path, encoding: str = "utf-8") -> list[str]:
    """Load a document file into Safari Writer's in-memory buffer format.

    Args:
        path: Path to the document file.
        encoding: Text encoding to use. Defaults to UTF-8.

    Returns:
        List of lines representing the document buffer.
    """
    ...
```

### Module Structure

- Use `from __future__ import annotations` in all files.
- Use `TYPE_CHECKING` for imports that are only used for type hints.
- Define `__all__` to explicitly list public exports.
- Use module-level constants in ALL_CAPS.

```python
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from safari_writer.state import AppState

__all__ = ["SomeClass", "some_function"]

DEFAULT_TAB_STOPS = set(range(5, 81, 5))
```

### State: Dataclasses

Use Python dataclasses for state objects. See `safari_writer/state.py` for examples.

```python
from dataclasses import dataclass, field


@dataclass
class AppState:
    buffer: list[str] = field(default_factory=lambda: [""])
    cursor_row: int = 0
    cursor_col: int = 0
```

### Screens: Textual Patterns

Screens follow specific Textual patterns:

1. **CSS as module-level constant** (not inline):

```python
EDITOR_CSS = """
EditorScreen {
    background: $surface;
}
#status-bar {
    dock: top;
    height: 1;
}
"""


class EditorScreen(Screen):
    CSS = EDITOR_CSS
```

2. **BINDINGS**: Define key bindings as a class attribute.

3. **compose()**: Use `ComposeResult` as the return type annotation.

```python
from textual.app import ComposeResult


def compose(self) -> ComposeResult:
    yield Static("Some text", id="status-bar")
    yield EditorArea(self.state)
```

4. **Constants**: Mode constants at module level:

```python
MODE_MENU = "menu"
MODE_HIGHLIGHT = "highlight"
```

## Testing

### Test Organization

- Tests live in `tests/` directory.
- Test files named `test_*.py`.
- Use pytest.
- Organize tests into classes by feature area.

```python
class TestTypeChar:
    def test_basic_insert(self):
        ...
```

### Testing UI Without a Running App

Use `unittest.mock.patch` to bypass Textual's Widget initialization. See `tests/test_editor.py` for the pattern:

```python
def make_editor(text: str = "") -> EditorArea:
    """Return an EditorArea with a fresh state, bypassing Textual Widget init."""
    state = AppState()
    state.buffer = text.split("\n") if text else [""]
    state.cursor_row = 0
    state.cursor_col = 0

    with patch("textual.widget.Widget.__init__", return_value=None):
        ed = EditorArea.__new__(EditorArea)
        ed.state = state
        ed.tab_stops = set(range(5, 81, 5))
        # Initialize other attrs...
    return ed
```

## Linting and Type Checking

Run before submitting:

```bash
# Full check (test + lint + typecheck)
make check

# Individual checks
make test
make lint
make mypy
```

Tools used:

- **ruff**: Formatting and quick linting
- **pylint**: Only E (errors), F (fatal), W0611 (undefined-name), W0612 (unused-vars)
- **mypy**: Strict type checking

## Cross-Platform Considerations

- Use `pathlib.Path` for all file operations.
- Use `/` in paths, not `\\`.
- Test on Windows primarily; avoid platform-specific code.
- Use `encoding="utf-8"` explicitly when reading/writing text files.

## File Organization

```
safari_writer/
    __init__.py
    main.py              # Entry point
    app.py               # Main App class
    state.py             # Dataclasses for state
    themes.py            # Theme definitions
    screens/
        __init__.py
        editor.py
        proofreader.py
        ...
    export_md.py
    format_codec.py
    ...
safari_dos/
    ...                  # Companion file browser app
tests/
    test_editor.py
    test_proofreader.py
    ...
```

## Adding a New Screen

1. Create `safari_writer/screens/new_feature.py`
2. Define CSS as `NEW_FEATURE_CSS` at module level
3. Define mode constants (e.g., `MODE_VIEW = "view"`)
4. Create class inheriting from `Screen`
5. Add BINDINGS, compose(), and handlers
6. Add docstrings to everything
7. Register in `app.py` if accessible from main menu
8. Write tests in `tests/test_new_feature.py`

## Adding a New Test

1. Create `tests/test_feature.py` (or add to existing test file)
2. Import the module under test
3. Import `pytest` and `unittest.mock`
4. Write helper constructors like `make_editor`
5. Organize tests into classes by feature
6. Use descriptive test method names: `test_*_does_*`

## What NOT to Do

- Don't invent new patterns — look at existing screens first
- Don't use inline CSS strings — use module-level constants
- Don't skip docstrings — Google style only
- Don't add new dependencies without discussion
- Don't use bare `python` — use `make` or `uv run`

## Getting Help

- Read specs in `spec/*.md` for feature requirements
- Check `TODO.md` for known tasks
