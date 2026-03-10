# LLMs: conserve tokens. Use the quiet default targets first.
# If something fails or you need more context, rerun the matching *-verbose target.
# Use the *-writer, *-dos, and *-all targets to scope work to one module or both.

WRITER_MODULE := safari_writer
DOS_MODULE := safari_dos
CHAT_MODULE := safari_chat
BASE_MODULE := safari_base
FED_MODULE := safari_fed
READER_MODULE := safari_reader
ALL_MODULES := $(WRITER_MODULE) $(DOS_MODULE) $(CHAT_MODULE) $(FED_MODULE) $(READER_MODULE)
PYTEST_COVERAGE_MODULES := $(WRITER_MODULE) $(DOS_MODULE) $(CHAT_MODULE) $(BASE_MODULE) $(FED_MODULE) $(READER_MODULE)
FORMAT_TARGETS := $(ALL_MODULES) tests

PYLINT_RULES := --disable=all --enable=E,F,W0611,W0612
UV_SYNC_DEFAULT_FLAGS := --quiet --no-progress
UV_SYNC_VERBOSE_FLAGS := --verbose
PYTEST_DEFAULT_FLAGS := -q --disable-warnings
PYTEST_VERBOSE_FLAGS := -v
PYTEST_COVERAGE_REPORT_FLAGS := --cov-report=term-missing --cov-report=xml:coverage.xml
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

.PHONY: locale locale-verbose \
	install install-verbose \
	run run-verbose run-writer run-writer-verbose run-dos run-dos-verbose run-chat run-chat-verbose run-fed run-fed-verbose run-reader run-reader-verbose \
	dev dev-verbose dev-writer dev-writer-verbose dev-dos dev-dos-verbose dev-chat dev-chat-verbose dev-fed dev-fed-verbose dev-reader dev-reader-verbose \
	test test-verbose coverage coverage-verbose tox tox-verbose check check-verbose \
	lint lint-verbose lint-all lint-all-verbose lint-writer lint-writer-verbose lint-dos lint-dos-verbose lint-chat lint-chat-verbose lint-fed lint-fed-verbose lint-reader lint-reader-verbose \
	lint-ruff lint-ruff-verbose lint-ruff-all lint-ruff-all-verbose lint-ruff-writer lint-ruff-writer-verbose lint-ruff-dos lint-ruff-dos-verbose lint-ruff-chat lint-ruff-chat-verbose lint-ruff-fed lint-ruff-fed-verbose lint-ruff-reader lint-ruff-reader-verbose \
	pylint pylint-verbose pylint-all pylint-all-verbose pylint-writer pylint-writer-verbose pylint-dos pylint-dos-verbose pylint-chat pylint-chat-verbose pylint-fed pylint-fed-verbose pylint-reader pylint-reader-verbose \
	mypy mypy-verbose mypy-all mypy-all-verbose mypy-writer mypy-writer-verbose mypy-dos mypy-dos-verbose mypy-chat mypy-chat-verbose mypy-fed mypy-fed-verbose mypy-reader mypy-reader-verbose \
	format format-verbose format-all format-all-verbose format-writer format-writer-verbose format-dos format-dos-verbose format-chat format-chat-verbose format-fed format-fed-verbose format-reader format-reader-verbose \
	publish publish-verbose

locale:
	@uv run --no-sync python scripts/compile_mo.py

locale-verbose:
	@uv run --no-sync python scripts/compile_mo.py

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

run-fed:
	@uv run --quiet safari-fed

run-fed-verbose:
	@uv run --verbose safari-fed

run-reader:
	@uv run --quiet safari-reader

run-reader-verbose:
	@uv run --verbose safari-reader

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

dev-fed:
	@uv run textual run safari_fed/main.py

dev-fed-verbose:
	@uv run textual run --dev safari_fed/main.py

dev-reader:
	@uv run textual run safari_reader/main.py

dev-reader-verbose:
	@uv run textual run --dev safari_reader/main.py

test:
	@uv run pytest tests/ $(PYTEST_DEFAULT_FLAGS)

test-verbose:
	@uv run pytest tests/ $(PYTEST_VERBOSE_FLAGS)

coverage:
	@uv run pytest tests/ $(PYTEST_DEFAULT_FLAGS) $(foreach module,$(PYTEST_COVERAGE_MODULES),--cov=$(module)) $(PYTEST_COVERAGE_REPORT_FLAGS)

coverage-verbose:
	@uv run pytest tests/ $(PYTEST_VERBOSE_FLAGS) $(foreach module,$(PYTEST_COVERAGE_MODULES),--cov=$(module)) $(PYTEST_COVERAGE_REPORT_FLAGS)

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

lint-fed: lint-ruff-fed pylint-fed

lint-fed-verbose: lint-ruff-fed-verbose pylint-fed-verbose

lint-reader: lint-ruff-reader pylint-reader

lint-reader-verbose: lint-ruff-reader-verbose pylint-reader-verbose

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

lint-ruff-fed:
	@uv run ruff check $(RUFF_CHECK_DEFAULT_FLAGS) $(FED_MODULE)

lint-ruff-fed-verbose:
	@uv run ruff check $(RUFF_CHECK_VERBOSE_FLAGS) $(FED_MODULE)

lint-ruff-reader:
	@uv run ruff check $(RUFF_CHECK_DEFAULT_FLAGS) $(READER_MODULE)

lint-ruff-reader-verbose:
	@uv run ruff check $(RUFF_CHECK_VERBOSE_FLAGS) $(READER_MODULE)

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

pylint-fed:
	@uv run pylint $(PYLINT_DEFAULT_FLAGS) $(FED_MODULE)

pylint-fed-verbose:
	@uv run pylint $(PYLINT_VERBOSE_FLAGS) $(FED_MODULE)

pylint-reader:
	@uv run pylint $(PYLINT_DEFAULT_FLAGS) $(READER_MODULE)

pylint-reader-verbose:
	@uv run pylint $(PYLINT_VERBOSE_FLAGS) $(READER_MODULE)

mypy: mypy-writer

mypy-verbose: mypy-writer-verbose

mypy-all: mypy-writer mypy-dos mypy-chat mypy-fed mypy-reader

mypy-all-verbose: mypy-writer-verbose mypy-dos-verbose mypy-chat-verbose mypy-fed-verbose mypy-reader-verbose

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

mypy-fed:
	@uv run mypy $(MYPY_DOS_CONFIG_FLAGS) $(MYPY_DEFAULT_FLAGS) $(FED_MODULE)

mypy-fed-verbose:
	@uv run mypy $(MYPY_DOS_CONFIG_FLAGS) $(MYPY_VERBOSE_FLAGS) $(FED_MODULE)

mypy-reader:
	@uv run mypy $(MYPY_DOS_CONFIG_FLAGS) $(MYPY_DEFAULT_FLAGS) $(READER_MODULE)

mypy-reader-verbose:
	@uv run mypy $(MYPY_DOS_CONFIG_FLAGS) $(MYPY_VERBOSE_FLAGS) $(READER_MODULE)

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

format-fed:
	@uv run ruff format $(RUFF_FORMAT_DEFAULT_FLAGS) $(FED_MODULE)

format-fed-verbose:
	@uv run ruff format $(RUFF_FORMAT_VERBOSE_FLAGS) $(FED_MODULE)

format-reader:
	@uv run ruff format $(RUFF_FORMAT_DEFAULT_FLAGS) $(READER_MODULE)

format-reader-verbose:
	@uv run ruff format $(RUFF_FORMAT_VERBOSE_FLAGS) $(READER_MODULE)

publish: test
	@uv run python -c "from pathlib import Path; import shutil; shutil.rmtree(Path('dist'), ignore_errors=True)"
	@uv run hatch -q build

publish-verbose: test-verbose
	@uv run python -c "from pathlib import Path; import shutil; shutil.rmtree(Path('dist'), ignore_errors=True)"
	@uv run hatch -v build
