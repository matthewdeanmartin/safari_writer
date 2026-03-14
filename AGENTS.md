# Safari Writer

Python + Textual TUI. `uv` manages env + deps.

## Workflow
- Prefer `make <target>` when it exists.
- Otherwise use `uv run ...`.
- Never use bare `python` or `pip`.

## Make
- Defaults are compact, use them to save token cost.
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
- Are you gpt/codex/copilot? You seem to be stuck using powershell.
- Specs: `spec/*.md`
- Skill: `.github/skills/session-sql-todos/SKILL.md` for session SQL / TODO tracking.
- Tests go in tests folder, use tmp_path for temporary files, don't creat throw away tests and delete them. Create permanent tests.