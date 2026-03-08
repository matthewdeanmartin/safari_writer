# Safari Writer

Python + Textual TUI. `uv` manages env + deps.

## Workflow
- Prefer `make <target>` when it exists.
- Otherwise use `uv run ...`.
- Never use bare `python` or `pip`.

## Make
- Defaults are compact. Use them first.
- Use `*-verbose` only when debugging.
- Use `*-writer`, `*-dos`, `*-all` to target one module or both.
- `install` / `install-verbose`
- `run`, `run-writer`, `run-dos` (+ `-verbose`)
- `dev`, `dev-writer`, `dev-dos` (+ `-verbose`)
- `test` / `test-verbose`
- `lint`, `lint-ruff`, `pylint` (+ `-writer` / `-dos` / `-all`, plus `-verbose`)
- `format` (+ `-writer` / `-dos` / `-all`, plus `-verbose`)
- `mypy` defaults to `safari_writer`; also `mypy-dos`, `mypy-all`, verbose variants
- `tox` / `tox-verbose`
- `check` / `check-verbose`
- `publish` / `publish-verbose`

## Notes
- Windows repo; commands may use git-bash syntax.
- Specs: `spec/*.md`
- TODO: `TODO.md`
- Skill: `.github/skills/session-sql-todos/SKILL.md` for session SQL / TODO tracking.
