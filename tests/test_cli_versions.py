"""CLI version flag coverage for standalone Safari apps."""

from __future__ import annotations

import pytest

from safari_base.main import build_parser as build_base_parser
from safari_chat.main import build_parser as build_chat_parser
from safari_reader.main import build_parser as build_reader_parser
from safari_repl.main import build_parser as build_repl_parser
from safari_slides.main import build_parser as build_slides_parser


@pytest.mark.parametrize(
    ("builder", "prog"),
    [
        (build_base_parser, "safari-base"),
        (build_chat_parser, "safari-chat"),
        (build_reader_parser, "safari-reader"),
        (build_repl_parser, "safari-repl"),
        (build_slides_parser, "safari-slides"),
    ],
)
def test_cli_version_flag_exits_cleanly(builder, prog, capsys):
    with pytest.raises(SystemExit) as excinfo:
        builder().parse_args(["--version"])

    captured = capsys.readouterr()
    assert excinfo.value.code == 0
    assert prog in captured.out
