"""CLI tests for Safari Writer."""

from __future__ import annotations

import json
from pathlib import Path

import safari_writer
import safari_writer.ansi_preview as ansi_preview
import safari_writer.app as app_module
import safari_writer.cli_types as cli_types
import safari_writer.document_io as document_io
import safari_writer.export_md as export_md_module
import safari_writer.export_ps as export_ps_module
import safari_writer.format_codec as format_codec
import safari_writer.mail_merge_db as mail_merge_db
import safari_writer.proofing as proofing
import safari_writer.state as state_module
from safari_writer.cli_types import StartupRequest
from safari_writer.main import build_startup_request, main, parse_args
from safari_writer.screens.editor import CTRL_BOLD, CTRL_MERGE


class FakeChecker:
    def __init__(self, bad_words: set[str] | None = None, suggestions: dict[str, list[str]] | None = None):
        self.bad_words = bad_words or set()
        self.suggestions = suggestions or {}

    def check(self, word: str) -> bool:
        return word.lower() not in self.bad_words

    def suggest(self, word: str) -> list[str]:
        return self.suggestions.get(word, [])


def test_parse_args_supports_bare_file_shorthand():
    args = parse_args(["draft.sfw"])

    assert args.command == "tui"
    assert args.tui_command == "edit"
    assert args.file == "draft.sfw"


def test_parse_args_supports_no_splash_flag():
    args = parse_args(["--no-splash"])

    assert args.no_splash is True


def test_public_package_exports_are_explicit():
    expected = {
        "AppState",
        "DEMO_DOCUMENT_RESOURCE",
        "GlobalFormat",
        "SafariWriterApp",
        "StartupRequest",
        "apply_mail_merge_to_buffer",
        "build_parser",
        "build_startup_request",
        "count_ansi_pages",
        "extract_ansi_page",
        "load_document_buffer",
        "load_demo_document_buffer",
        "load_mail_merge_db",
        "parse_args",
        "render_ansi_preview",
        "run_cli",
    }

    assert expected.issubset(set(safari_writer.__all__))


def test_public_submodule_exports_are_explicit():
    assert cli_types.__all__ == ["StartupRequest"]
    assert document_io.__all__ == [
        "DEMO_DOCUMENT_RESOURCE",
        "load_demo_document_buffer",
        "load_document_buffer",
        "load_document_state",
        "serialize_document_buffer",
    ]
    assert ansi_preview.__all__ == [
        "count_ansi_pages",
        "extract_ansi_page",
        "render_ansi_preview",
    ]
    assert app_module.__all__ == ["SafariWriterApp"]
    assert export_md_module.__all__ == ["export_markdown"]
    assert export_ps_module.__all__ == ["export_postscript"]
    assert format_codec.__all__ == [
        "decode_sfw",
        "encode_sfw",
        "has_controls",
        "is_sfw",
        "strip_controls",
    ]
    assert state_module.__all__ == ["AppState", "GlobalFormat"]
    assert proofing.__all__ == [
        "check_word",
        "dict_lookup",
        "extract_words",
        "load_personal_dictionary",
        "make_checker",
        "suggest_words",
    ]
    assert "apply_mail_merge_to_buffer" in mail_merge_db.__all__


def test_main_rejects_invalid_edit_combination(capsys):
    exit_code = main(["tui", "edit", "--file", "demo.sfw", "--new"])

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "not allowed with argument" in captured.err


def test_build_startup_request_for_proofreader():
    args = parse_args(
        [
            "tui",
            "proofreader",
            "--file",
            "draft.sfw",
            "--mode",
            "correct",
            "--personal-dict",
            "user.txt",
        ]
    )

    request = build_startup_request(args)

    assert request == StartupRequest(
        destination="proofreader",
        document_path=Path("draft.sfw").resolve(),
        proofreader_mode="correct",
        read_only=False,
        personal_dict_paths=(Path("user.txt").resolve(),),
    )


def test_build_startup_request_for_safari_dos():
    args = parse_args(["tui", "safari-dos", "--path", "docs"])

    request = build_startup_request(args)

    assert request == StartupRequest(
        destination="safari_dos",
        safari_dos_path=Path("docs").resolve(),
    )


def test_main_default_invocation_launches_menu(monkeypatch):
    captured: dict[str, object] = {}
    splash_calls: list[bool] = []

    def fake_launch(state, request, args):
        captured["state"] = state
        captured["request"] = request
        return 0

    monkeypatch.setattr("safari_writer.main.maybe_show_splash", lambda *, no_splash: splash_calls.append(no_splash))
    monkeypatch.setattr("safari_writer.main._launch_tui", fake_launch)

    exit_code = main([])

    assert exit_code == 0
    assert splash_calls == [False]
    assert captured["request"] == StartupRequest(destination="menu")


def test_main_passes_no_splash_flag_to_tui_launch(monkeypatch):
    splash_calls: list[bool] = []

    monkeypatch.setattr("safari_writer.main.maybe_show_splash", lambda *, no_splash: splash_calls.append(no_splash))
    monkeypatch.setattr("safari_writer.main._launch_tui", lambda state, request, args: 0)

    exit_code = main(["--no-splash"])

    assert exit_code == 0
    assert splash_calls == [True]


def test_main_tui_edit_loads_file_and_request(monkeypatch, tmp_path):
    captured: dict[str, object] = {}
    document = tmp_path / "draft.sfw"
    document.write_text("Hello")

    def fake_launch(state, request, args):
        captured["state"] = state
        captured["request"] = request
        return 0

    monkeypatch.setattr("safari_writer.main._launch_tui", fake_launch)

    exit_code = main(["tui", "edit", "--file", str(document), "--cursor-line", "2", "--cursor-column", "3"])

    assert exit_code == 0
    assert captured["request"].destination == "edit"
    assert captured["state"].filename == str(document.resolve())
    assert captured["state"].buffer == ["Hello"]


def test_main_honors_cwd_for_bare_file(monkeypatch, tmp_path):
    captured: dict[str, object] = {}
    subdir = tmp_path / "docs"
    subdir.mkdir()
    document = subdir / "draft.sfw"
    document.write_text("Hello")

    def fake_launch(state, request, args):
        captured["state"] = state
        captured["request"] = request
        return 0

    monkeypatch.setattr("safari_writer.main._launch_tui", fake_launch)

    exit_code = main(["--cwd", str(subdir), "draft.sfw"])

    assert exit_code == 0
    assert captured["state"].filename == str(document.resolve())


def test_export_markdown_stdout(capsys, tmp_path):
    document = tmp_path / "draft.sfw"
    document.write_text(f"{CTRL_BOLD}hello{CTRL_BOLD}")

    exit_code = main(["export", "markdown", str(document), "--stdout"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "**hello**" in captured.out


def test_export_markdown_applies_mail_merge_database(capsys, tmp_path):
    document = tmp_path / "draft.sfw"
    database = tmp_path / "contacts.json"
    document.write_text(f"Dear {CTRL_MERGE}1")
    database.write_text(
        json.dumps(
            {
                "fields": [{"name": "Name", "max_len": 20}],
                "records": [["Pat"]],
            }
        )
    )

    exit_code = main(["export", "markdown", str(document), "--merge-db", str(database), "--stdout"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Dear Pat" in captured.out


def test_export_ansi_rejects_out_of_range_page(capsys, tmp_path):
    document = tmp_path / "draft.txt"
    document.write_text("Hello")

    exit_code = main(["export", "ansi", str(document), "--page", "2"])

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "out of range" in captured.err


def test_proof_check_exit_codes(monkeypatch, capsys, tmp_path):
    document = tmp_path / "draft.txt"
    document.write_text("teh word")
    monkeypatch.setattr("safari_writer.main.make_checker", lambda: FakeChecker({"teh"}))

    exit_code = main(["proof", "check", str(document)])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "1 spelling error" in captured.out


def test_proof_list_json(monkeypatch, capsys, tmp_path):
    document = tmp_path / "draft.txt"
    document.write_text("teh word")
    monkeypatch.setattr("safari_writer.main.make_checker", lambda: FakeChecker({"teh"}))

    exit_code = main(["proof", "list", str(document), "--json"])

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload == [{"line": 1, "column": 1, "token": "teh"}]


def test_proof_suggest_outputs_candidates(monkeypatch, capsys):
    monkeypatch.setattr(
        "safari_writer.main.make_checker",
        lambda: FakeChecker(suggestions={"teh": ["the", "tech"]}),
    )

    exit_code = main(["proof", "suggest", "teh"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out.splitlines() == ["the", "tech"]


def test_format_commands_round_trip(tmp_path):
    text_file = tmp_path / "draft.txt"
    text_file.write_text("Hello")
    encoded = tmp_path / "draft.sfw"
    decoded = tmp_path / "draft.decoded.txt"
    stripped = tmp_path / "draft.stripped.txt"

    assert main(["--quiet", "format", "encode", str(text_file), "-o", str(encoded)]) == 0
    assert encoded.read_text() == "Hello"
    assert main(["--quiet", "format", "decode", str(encoded), "-o", str(decoded)]) == 0
    assert decoded.read_text() == "Hello"

    encoded.write_text(f"{CTRL_BOLD}Hello{CTRL_BOLD}")
    assert main(["--quiet", "format", "strip", str(encoded), "-o", str(stripped)]) == 0
    assert stripped.read_text() == "Hello"


def test_mail_merge_inspect_and_subset_json(capsys, tmp_path):
    database = tmp_path / "contacts.json"
    database.write_text(
        json.dumps(
            {
                "fields": [
                    {"name": "State", "max_len": 10},
                    {"name": "Name", "max_len": 20},
                ],
                "records": [["AL", "Ann"], ["TX", "Tom"], ["AZ", "Ava"]],
            }
        )
    )

    inspect_code = main(["mail-merge", "inspect", str(database), "--json"])
    inspect_payload = json.loads(capsys.readouterr().out)
    subset_code = main(
        ["mail-merge", "subset", str(database), "--field", "1", "--low", "A", "--high", "B", "--json"]
    )
    subset_payload = json.loads(capsys.readouterr().out)

    assert inspect_code == 0
    assert inspect_payload["record_count"] == 3
    assert subset_code == 0
    assert subset_payload["matching_indexes"] == [1, 3]


def test_mail_merge_append_and_validate(tmp_path):
    base = tmp_path / "base.json"
    other = tmp_path / "other.json"
    merged = tmp_path / "merged.json"
    invalid = tmp_path / "invalid.json"
    payload = {
        "fields": [{"name": "Name", "max_len": 20}],
        "records": [["Ann"]],
    }
    base.write_text(json.dumps(payload))
    other.write_text(json.dumps({"fields": payload["fields"], "records": [["Bob"]]}))
    invalid.write_text(json.dumps({"fields": [], "records": []}))

    assert main(["--quiet", "mail-merge", "append", str(base), str(other), "-o", str(merged)]) == 0
    merged_payload = json.loads(merged.read_text())
    assert merged_payload["records"] == [["Ann"], ["Bob"]]
    assert main(["--quiet", "mail-merge", "validate", str(merged)]) == 0
    assert main(["--quiet", "mail-merge", "validate", str(invalid)]) == 1
