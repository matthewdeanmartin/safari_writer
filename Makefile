.PHONY: install run dev lint clean

install:
	uv sync

run:
	uv run safari-writer

dev:
	uv run textual run --dev safari_writer/main.py

test:
	uv run pytest tests/ -v

lint:
	uv run ruff check safari_writer/

clean:
	rm -rf .venv __pycache__ safari_writer/__pycache__ safari_writer/screens/__pycache__
