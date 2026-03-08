# LLMs: conserve tokens. Use the quiet default targets first.
# If something fails or you need more context, rerun the matching *-verbose target.
# Use the *-writer, *-dos, and *-all targets to scope work to one module or both.

WRITER_MODULE := safari_writer
DOS_MODULE := safari_dos
CHAT_MODULE := safari_chat
ALL_MODULES := $(WRITER_MODULE) $(DOS_MODULE) $(CHAT_MODULE)
FORMAT_TARGETS := $(ALL_MODULES) tests

PYLINT_RULES := --disable=all --enable=E,F,W0611,W0612
UV_SYNC_DEFAULT_FLAGS := --quiet --no-progress
UV_SYNC_VERBOSE_FLAGS := --verbose
PYTEST_DEFAULT_FLAGS := -q --disable-warnings
PYTEST_VERBOSE_FLAGS := -v
RUFF_CHECK_DEFAULT_FLAGS := --quiet --fix
RUFF_CHECK_VERBOSE_FLAGS := --verbose --fix
RUFF_FORMAT_DEFAULT_FLAGS := --quiet
RUFF_FORMAT_VERBOSE_FLAGS := --verbose
PYLINT_DEFAULT_FLAGS := $(PYLINT_RULES) --score=n --reports=n
PYLINT_VERBOSE_FLAGS := -v $(PYLINT_RULES)
MYPY_DEFAULT_FLAGS := --no-pretty --hide-error-context --no-error-summary
MYPY_VERBOSE_FLAGS := -v
MYPY_DOS_CONFIG_FLAGS := --config-file NUL
TOX_DEFAULT_FLAGS := -q
TOX_VERBOSE_FLAGS := -v

.PHONY: install install-verbose \
	run run-verbose run-writer run-writer-verbose run-dos run-dos-verbose run-chat run-chat-verbose \
	dev dev-verbose dev-writer dev-writer-verbose dev-dos dev-dos-verbose dev-chat dev-chat-verbose \
	test test-verbose tox tox-verbose check check-verbose \
	lint lint-verbose lint-all lint-all-verbose lint-writer lint-writer-verbose lint-dos lint-dos-verbose lint-chat lint-chat-verbose \
	lint-ruff lint-ruff-verbose lint-ruff-all lint-ruff-all-verbose lint-ruff-writer lint-ruff-writer-verbose lint-ruff-dos lint-ruff-dos-verbose lint-ruff-chat lint-ruff-chat-verbose \
	pylint pylint-verbose pylint-all pylint-all-verbose pylint-writer pylint-writer-verbose pylint-dos pylint-dos-verbose pylint-chat pylint-chat-verbose \
	mypy mypy-verbose mypy-all mypy-all-verbose mypy-writer mypy-writer-verbose mypy-dos mypy-dos-verbose mypy-chat mypy-chat-verbose \
	format format-verbose format-all format-all-verbose format-writer format-writer-verbose format-dos format-dos-verbose format-chat format-chat-verbose \
	publish publish-verbose

install:
	@uv sync $(UV_SYNC_DEFAULT_FLAGS)

install-verbose:
	@uv sync $(UV_SYNC_VERBOSE_FLAGS)

run: run-writer

run-verbose: run-writer-verbose

run-writer:
	@uv run safari-writer --quiet

run-writer-verbose:
	@uv run safari-writer --verbose

run-dos:
	@uv run --quiet safari-dos

run-dos-verbose:
	@uv run --verbose safari-dos

run-chat:
	@uv run --quiet safari-chat

run-chat-verbose:
	@uv run --verbose safari-chat

dev: dev-writer

dev-verbose: dev-writer-verbose

dev-writer:
	@uv run textual run safari_writer/main.py

dev-writer-verbose:
	@uv run textual run --dev safari_writer/main.py

dev-dos:
	@uv run textual run safari_dos/main.py

dev-dos-verbose:
	@uv run textual run --dev safari_dos/main.py

dev-chat:
	@uv run textual run safari_chat/main.py

dev-chat-verbose:
	@uv run textual run --dev safari_chat/main.py

test:
	@uv run pytest tests/ $(PYTEST_DEFAULT_FLAGS)

test-verbose:
	@uv run pytest tests/ $(PYTEST_VERBOSE_FLAGS)

tox:
	@uv run tox $(TOX_DEFAULT_FLAGS)

tox-verbose:
	@uv run tox $(TOX_VERBOSE_FLAGS)

check: test lint mypy

check-verbose: test-verbose lint-verbose mypy-verbose

lint: lint-all

lint-verbose: lint-all-verbose

lint-all: lint-ruff-all pylint-all

lint-all-verbose: lint-ruff-all-verbose pylint-all-verbose

lint-writer: lint-ruff-writer pylint-writer

lint-writer-verbose: lint-ruff-writer-verbose pylint-writer-verbose

lint-dos: lint-ruff-dos pylint-dos

lint-dos-verbose: lint-ruff-dos-verbose pylint-dos-verbose

lint-chat: lint-ruff-chat pylint-chat

lint-chat-verbose: lint-ruff-chat-verbose pylint-chat-verbose

lint-ruff: lint-ruff-all

lint-ruff-verbose: lint-ruff-all-verbose

lint-ruff-all:
	@uv run ruff check $(RUFF_CHECK_DEFAULT_FLAGS) $(ALL_MODULES)

lint-ruff-all-verbose:
	@uv run ruff check $(RUFF_CHECK_VERBOSE_FLAGS) $(ALL_MODULES)

lint-ruff-writer:
	@uv run ruff check $(RUFF_CHECK_DEFAULT_FLAGS) $(WRITER_MODULE)

lint-ruff-writer-verbose:
	@uv run ruff check $(RUFF_CHECK_VERBOSE_FLAGS) $(WRITER_MODULE)

lint-ruff-dos:
	@uv run ruff check $(RUFF_CHECK_DEFAULT_FLAGS) $(DOS_MODULE)

lint-ruff-dos-verbose:
	@uv run ruff check $(RUFF_CHECK_VERBOSE_FLAGS) $(DOS_MODULE)

lint-ruff-chat:
	@uv run ruff check $(RUFF_CHECK_DEFAULT_FLAGS) $(CHAT_MODULE)

lint-ruff-chat-verbose:
	@uv run ruff check $(RUFF_CHECK_VERBOSE_FLAGS) $(CHAT_MODULE)

pylint: pylint-all

pylint-verbose: pylint-all-verbose

pylint-all:
	@uv run pylint $(PYLINT_DEFAULT_FLAGS) $(ALL_MODULES)

pylint-all-verbose:
	@uv run pylint $(PYLINT_VERBOSE_FLAGS) $(ALL_MODULES)

pylint-writer:
	@uv run pylint $(PYLINT_DEFAULT_FLAGS) $(WRITER_MODULE)

pylint-writer-verbose:
	@uv run pylint $(PYLINT_VERBOSE_FLAGS) $(WRITER_MODULE)

pylint-dos:
	@uv run pylint $(PYLINT_DEFAULT_FLAGS) $(DOS_MODULE)

pylint-dos-verbose:
	@uv run pylint $(PYLINT_VERBOSE_FLAGS) $(DOS_MODULE)

pylint-chat:
	@uv run pylint $(PYLINT_DEFAULT_FLAGS) $(CHAT_MODULE)

pylint-chat-verbose:
	@uv run pylint $(PYLINT_VERBOSE_FLAGS) $(CHAT_MODULE)

mypy: mypy-writer

mypy-verbose: mypy-writer-verbose

mypy-all: mypy-writer mypy-dos

mypy-all-verbose: mypy-writer-verbose mypy-dos-verbose

mypy-writer:
	@uv run mypy $(MYPY_DEFAULT_FLAGS) $(WRITER_MODULE)

mypy-writer-verbose:
	@uv run mypy $(MYPY_VERBOSE_FLAGS) $(WRITER_MODULE)

mypy-dos:
	@uv run mypy $(MYPY_DOS_CONFIG_FLAGS) $(MYPY_DEFAULT_FLAGS) $(DOS_MODULE)

mypy-dos-verbose:
	@uv run mypy $(MYPY_DOS_CONFIG_FLAGS) $(MYPY_VERBOSE_FLAGS) $(DOS_MODULE)

mypy-chat:
	@uv run mypy $(MYPY_DOS_CONFIG_FLAGS) $(MYPY_DEFAULT_FLAGS) $(CHAT_MODULE)

mypy-chat-verbose:
	@uv run mypy $(MYPY_DOS_CONFIG_FLAGS) $(MYPY_VERBOSE_FLAGS) $(CHAT_MODULE)

format: format-all

format-verbose: format-all-verbose

format-all:
	@uv run ruff format $(RUFF_FORMAT_DEFAULT_FLAGS) $(FORMAT_TARGETS)

format-all-verbose:
	@uv run ruff format $(RUFF_FORMAT_VERBOSE_FLAGS) $(FORMAT_TARGETS)

format-writer:
	@uv run ruff format $(RUFF_FORMAT_DEFAULT_FLAGS) $(WRITER_MODULE)

format-writer-verbose:
	@uv run ruff format $(RUFF_FORMAT_VERBOSE_FLAGS) $(WRITER_MODULE)

format-dos:
	@uv run ruff format $(RUFF_FORMAT_DEFAULT_FLAGS) $(DOS_MODULE)

format-dos-verbose:
	@uv run ruff format $(RUFF_FORMAT_VERBOSE_FLAGS) $(DOS_MODULE)

format-chat:
	@uv run ruff format $(RUFF_FORMAT_DEFAULT_FLAGS) $(CHAT_MODULE)

format-chat-verbose:
	@uv run ruff format $(RUFF_FORMAT_VERBOSE_FLAGS) $(CHAT_MODULE)

publish: test
	@uv run python -c "from pathlib import Path; import shutil; shutil.rmtree(Path('dist'), ignore_errors=True)"
	@uv run hatch -q build

publish-verbose: test-verbose
	@uv run python -c "from pathlib import Path; import shutil; shutil.rmtree(Path('dist'), ignore_errors=True)"
	@uv run hatch -v build
