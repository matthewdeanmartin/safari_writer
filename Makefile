.PHONY: install run dev test check lint lint-ruff pylint format mypy tox

install:
	uv sync

run:
	uv run safari-writer

dev:
	uv run textual run --dev safari_writer/main.py

test:
	uv run pytest tests/ -v

tox:
	uv run tox

check: test lint mypy

lint:
	uv run ruff check safari_writer/ --fix
	uv run ruff check safari_dos --fix
	uv run pylint safari_writer --disable=all --enable=E,F,W0611,W0612

lint-ruff:
	uv run ruff check safari_writer/ --fix
	uv run ruff check safari_dos --fix

pylint:
	uv run pylint safari_writer --disable=all --enable=E,F,W0611,W0612

mypy:
	uv run mypy safari_writer

format:
	uv run ruff format safari_writer/ tests/

.PHONY: publish
publish: test
	rm -rf dist && hatch build
