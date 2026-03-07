# Safari Writer

Python + Textual TUI. Uses `uv` for deps/venv.

## Running code

- **Always use `uv run`** to execute Python: `uv run python -c "..."`, `uv run pytest`, etc.
- **Never use bare `python` or `pip`** — the venv is managed by uv.
- `make test` = `uv run pytest tests/ -v`
- `make run` = `uv run safari-writer`
- `make dev` = `uv run textual run --dev safari_writer/main.py`
- `make install` = `uv sync`

## Environment

- Platform: Windows, shell is git-bash (use Unix paths/syntax)
- Spec files: `spec/*.md`
- TODO: `TODO.md`
