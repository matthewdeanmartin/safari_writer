# Safari Writer

Python + Textual TUI. `uv` manages env + deps.

## Workflow

- Prefer `make <target>` when a target exists.
- Otherwise use `uv run ...`.
- Never use bare `python` or `pip`.

## Makefile

- `make install` -> `uv sync`
- `make run` -> `uv run safari-writer`
- `make dev` -> `uv run textual run --dev safari_writer/main.py`
- `make test` -> `uv run pytest tests/ -v`
- `make lint` -> `uv run ruff check safari_writer/` + `uv run pylint safari_writer --disable=all --enable=E,F,W0611,W0612`
- `make lint-ruff` -> `uv run ruff check safari_writer/`
- `make pylint` -> `uv run pylint safari_writer --disable=all --enable=E,F,W0611,W0612`
- `make format` -> `uv run ruff format safari_writer/ tests/`
- `make mypy` -> `uv run mypy safari_writer`
- `make check` -> `make test` + `make lint` + `make mypy`

## Repo notes

- Windows repo; commands often run in git-bash syntax.
- Specs: `spec/*.md`
- TODO: `TODO.md`
