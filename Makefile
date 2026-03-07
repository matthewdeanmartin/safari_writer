.PHONY: install run dev test check lint lint-ruff pylint format

install:
	uv sync

run:
	uv run safari-writer

dev:
	uv run textual run --dev safari_writer/main.py

test:
	uv run pytest tests/ -v

check: test lint

lint:
	uv run ruff check safari_writer/
	uv run pylint safari_writer --disable=all --enable=E,F,W0611,W0612

lint-ruff:
	uv run ruff check safari_writer/

pylint:
	uv run pylint safari_writer --disable=all --enable=E,F,W0611,W0612

format:
	uv run ruff format safari_writer/ tests/
