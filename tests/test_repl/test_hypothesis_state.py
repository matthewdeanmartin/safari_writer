"""Property-based tests for non-UI Safari REPL state helpers."""

from __future__ import annotations

import string

from hypothesis import given
from hypothesis import strategies as st

from safari_repl.main import parse_args
from safari_repl.state import ReplState

ARG_TEXT = st.text(
    alphabet=string.ascii_letters + string.digits + "._-\\/",
    min_size=1,
    max_size=40,
).filter(lambda value: not value.startswith("-"))
LINE_TEXT = st.text(
    alphabet=st.characters(blacklist_characters="\r\n", blacklist_categories=("Cs",)),
    max_size=20,
)


@given(ARG_TEXT)
def test_parse_args_preserves_file_argument(path_text: str) -> None:
    args = parse_args([path_text])

    assert args.file == path_text


@given(st.lists(LINE_TEXT, max_size=8), st.lists(LINE_TEXT, max_size=8))
def test_repl_state_instances_do_not_share_default_lists(
    history: list[str], output_lines: list[str]
) -> None:
    first = ReplState()
    second = ReplState()

    first.history.extend(history)
    first.output_lines.extend(output_lines)

    assert second.history == []
    assert second.output_lines == []
