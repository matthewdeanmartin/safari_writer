"""Tests for Safari DOS."""

from __future__ import annotations

import importlib
from pathlib import Path

import safari_dos
from safari_dos.main import main as safari_dos_main, parse_args
from safari_dos.services import (
    create_folder,
    duplicate_path,
    list_directory,
    list_garbage,
    move_to_garbage,
    rename_path,
    restore_from_garbage,
)
from safari_dos.state import SafariDosExitRequest


def test_public_exports_are_explicit():
    expected = {
        "SafariDosApp",
        "SafariDosExitRequest",
        "SafariDosState",
        "build_parser",
        "create_folder",
        "discover_locations",
        "duplicate_path",
        "list_directory",
        "list_garbage",
        "main",
        "move_to_garbage",
        "parse_args",
        "rename_path",
        "restore_from_garbage",
    }

    assert expected.issubset(set(safari_dos.__all__))


def test_parse_args_supports_optional_start_path():
    args = parse_args(["docs"])

    assert args.path == "docs"


def test_list_directory_filters_hidden_files(tmp_path):
    visible = tmp_path / "draft.txt"
    hidden = tmp_path / ".secret.txt"
    visible.write_text("hello", encoding="utf-8")
    hidden.write_text("quiet", encoding="utf-8")

    visible_entries = list_directory(tmp_path)
    hidden_entries = list_directory(tmp_path, show_hidden=True)

    assert [entry.name for entry in visible_entries] == ["draft.txt"]
    assert {entry.name for entry in hidden_entries} == {"draft.txt", ".secret.txt"}


def test_duplicate_path_generates_copy_name(tmp_path):
    source = tmp_path / "chapter01.txt"
    source.write_text("draft", encoding="utf-8")

    duplicate = duplicate_path(source)

    assert duplicate.name == "chapter01 COPY.txt"
    assert duplicate.read_text(encoding="utf-8") == "draft"


def test_move_to_garbage_and_restore_round_trip(tmp_path, monkeypatch):
    monkeypatch.setenv("SAFARI_DOS_HOME", str(tmp_path / "support"))
    source = tmp_path / "notes.txt"
    source.write_text("remember", encoding="utf-8")

    entry = move_to_garbage(source)

    assert not source.exists()
    assert entry.name == "notes.txt"
    assert [item.name for item in list_garbage()] == ["notes.txt"]

    restored = restore_from_garbage(entry.item_id)

    assert restored == source
    assert restored.read_text(encoding="utf-8") == "remember"
    assert list_garbage() == []


def test_create_folder_and_rename_path(tmp_path):
    folder = create_folder(tmp_path, "Drafts")
    renamed = rename_path(folder, "Revisions")

    assert renamed == tmp_path / "Revisions"
    assert renamed.is_dir()


def test_main_launches_writer_when_app_requests_handoff(monkeypatch, tmp_path):
    document = tmp_path / "draft.sfw"
    document.write_text("Hello", encoding="utf-8")
    launched: list[list[str]] = []
    safari_dos_main_module = importlib.import_module("safari_dos.main")
    safari_writer_main_module = importlib.import_module("safari_writer.main")

    class FakeApp:
        def __init__(self, start_path: Path | None = None) -> None:
            self.start_path = start_path

        def run(self):
            return SafariDosExitRequest(action="open-in-writer", document_path=document)

    monkeypatch.setattr(safari_dos_main_module, "SafariDosApp", FakeApp)
    monkeypatch.setattr(safari_writer_main_module, "main", lambda argv: launched.append(argv) or 0)

    exit_code = safari_dos_main([str(tmp_path)])

    assert exit_code == 0
    assert launched == [["tui", "edit", "--file", str(document)]]
