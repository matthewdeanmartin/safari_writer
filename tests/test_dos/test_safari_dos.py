"""Tests for Safari DOS."""

from __future__ import annotations

import importlib
from pathlib import Path

import safari_dos
from safari_dos.main import main as safari_dos_main, parse_args
from safari_dos.state import SafariDosLaunchConfig, SafariDosState
from safari_dos.screens import SafariDosBrowserScreen
from safari_dos.services import (
    copy_paths,
    create_folder,
    discover_locations,
    duplicate_path,
    get_entry_info,
    get_preview_text,
    list_favorites,
    list_directory,
    list_garbage,
    list_recent_documents,
    list_recent_locations,
    move_paths,
    move_to_garbage,
    record_recent_document,
    record_recent_location,
    rename_path,
    restore_from_garbage,
    set_protected,
    toggle_favorite,
    unzip_path,
    zip_paths,
)
import unittest.mock as mock
from safari_dos.state import SafariDosExitRequest
from safari_writer.app import SafariWriterApp
from safari_writer.screens.file_ops import FilePromptScreen


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

    assert args.command == "menu"
    assert args.path == "docs"


def test_parse_args_supports_browse_startup_flags():
    args = parse_args(
        [
            "browse",
            "docs",
            "--show-hidden",
            "--sort",
            "size",
            "--descending",
            "--filter",
            "draft",
            "--select",
            "draft.sfw",
        ]
    )

    assert args.command == "browse"
    assert args.path == "docs"
    assert args.show_hidden is True
    assert args.sort == "size"
    assert args.descending is True
    assert args.filter == "draft"
    assert args.select == "draft.sfw"


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


def test_move_to_garbage_sends_to_os_trash(tmp_path):
    source = tmp_path / "notes.txt"
    source.write_text("remember", encoding="utf-8")

    with mock.patch("send2trash.send2trash") as mocked_send:
        entry = move_to_garbage(source)

    mocked_send.assert_called_once_with(str(source))
    assert entry.name == "notes.txt"


def test_list_garbage_returns_empty():
    assert list_garbage() == []


def test_restore_from_garbage_raises_always():
    import pytest

    with pytest.raises(FileNotFoundError):
        restore_from_garbage("any-id")


def test_create_folder_and_rename_path(tmp_path):
    folder = create_folder(tmp_path, "Drafts")
    renamed = rename_path(folder, "Revisions")

    assert renamed == tmp_path / "Revisions"
    assert renamed.is_dir()


def test_set_protected_round_trip(tmp_path):
    draft = tmp_path / "draft.txt"
    draft.write_text("hello", encoding="utf-8")

    set_protected(draft, True)
    protected_entry = next(
        entry for entry in list_directory(tmp_path) if entry.name == "draft.txt"
    )
    assert protected_entry.protected is True

    set_protected(draft, False)
    unprotected_entry = next(
        entry for entry in list_directory(tmp_path) if entry.name == "draft.txt"
    )
    assert unprotected_entry.protected is False


def test_recent_and_favorite_locations_persist(tmp_path, monkeypatch):
    monkeypatch.setenv("SAFARI_DOS_HOME", str(tmp_path / "support"))
    project = tmp_path / "Project"
    project.mkdir()
    archive = tmp_path / "Archive"
    archive.mkdir()
    document = project / "draft.sfw"
    document.write_text("hello", encoding="utf-8")

    assert toggle_favorite(project) is True
    assert list_favorites() == [project.resolve()]

    recent_locations = record_recent_location(project)
    record_recent_location(archive)
    recent_documents = record_recent_document(document)

    assert recent_locations[0] == project.resolve()
    assert list_recent_locations()[0] == archive.resolve()
    assert recent_documents[0] == document.resolve()
    assert list_recent_documents()[0] == document.resolve()


def test_writer_load_and_delete_actions_use_safari_dos(monkeypatch):
    app = SafariWriterApp()
    pushed: list[tuple[object, object | None]] = []

    monkeypatch.setattr(
        app,
        "push_screen",
        lambda screen, callback=None, **_: pushed.append((screen, callback)),
    )

    app.handle_menu_action("load")
    app.handle_menu_action("delete")

    assert isinstance(pushed[0][0], SafariDosBrowserScreen)
    assert pushed[0][0]._picker_mode == "file"
    assert isinstance(pushed[1][0], SafariDosBrowserScreen)
    assert pushed[1][0]._picker_mode == "file"


def test_writer_save_uses_safari_dos_directory_picker(monkeypatch):
    app = SafariWriterApp()
    pushed: list[tuple[object, object | None]] = []

    monkeypatch.setattr(
        app,
        "push_screen",
        lambda screen, callback=None, **_: pushed.append((screen, callback)),
    )

    app.handle_menu_action("save")
    assert isinstance(pushed[0][0], FilePromptScreen)

    app._on_choose_save_name("draft.sfw")

    assert isinstance(pushed[1][0], SafariDosBrowserScreen)
    assert pushed[1][0]._picker_mode == "directory"


def test_writer_delete_moves_file_to_garbage(tmp_path):
    draft = tmp_path / "draft.sfw"
    draft.write_text("hello", encoding="utf-8")
    app = SafariWriterApp()
    app._pending_delete_path = draft

    with mock.patch("send2trash.send2trash") as mocked_send:
        app._on_delete_confirm(True)

    mocked_send.assert_called_once_with(str(draft))


def test_main_launches_writer_when_app_requests_handoff(monkeypatch, tmp_path):
    document = tmp_path / "draft.sfw"
    document.write_text("Hello", encoding="utf-8")
    launched: list[list[str]] = []
    safari_dos_main_module = importlib.import_module("safari_dos.main")
    safari_writer_main_module = importlib.import_module("safari_writer.main")

    class FakeApp:
        def __init__(
            self,
            start_path: Path | None = None,
            *,
            state: SafariDosState | None = None,
            launch_config: SafariDosLaunchConfig | None = None,
        ) -> None:
            self.start_path = start_path

        def run(self):
            return SafariDosExitRequest(action="open-in-writer", document_path=document)

    monkeypatch.setattr(safari_dos_main_module, "SafariDosApp", FakeApp)
    monkeypatch.setattr(
        safari_writer_main_module, "main", lambda argv: launched.append(argv) or 0
    )

    exit_code = safari_dos_main([str(tmp_path)])

    assert exit_code == 0
    assert launched == [["tui", "edit", "--file", str(document)]]


def test_main_browse_launches_with_startup_state(monkeypatch, tmp_path):
    selected = tmp_path / "draft.sfw"
    selected.write_text("Hello", encoding="utf-8")
    captured: dict[str, object] = {}
    safari_dos_main_module = importlib.import_module("safari_dos.main")

    class FakeApp:
        def __init__(
            self,
            start_path: Path | None = None,
            *,
            state: SafariDosState | None = None,
            launch_config: SafariDosLaunchConfig | None = None,
        ) -> None:
            captured["start_path"] = start_path
            captured["state"] = state
            captured["launch_config"] = launch_config

        def run(self):
            captured["ran"] = True
            return None

    monkeypatch.setattr(safari_dos_main_module, "SafariDosApp", FakeApp)

    exit_code = safari_dos_main(
        [
            "browse",
            str(tmp_path),
            "--show-hidden",
            "--preview",
            "fullscreen",
            "--sort",
            "date",
            "--descending",
            "--filter",
            "draft",
            "--select",
            "draft.sfw",
        ]
    )

    assert exit_code == 0
    state = captured["state"]
    launch = captured["launch_config"]
    assert state.current_path == tmp_path.resolve()
    assert state.show_hidden is True
    assert state.show_preview is True
    assert state.fullscreen_preview is True
    assert state.sort_field == "date"
    assert state.ascending is False
    assert state.filter_text == "draft"
    assert launch.initial_screen == "browser"
    assert launch.selected_path == selected.resolve()
    assert captured["ran"] is True


def test_main_ls_lists_directory_entries(tmp_path, capsys):
    folder = tmp_path / "folder"
    folder.mkdir()
    doc = tmp_path / "doc.txt"
    doc.write_text("hello", encoding="utf-8")

    exit_code = safari_dos_main(["ls", str(tmp_path), "--sort", "name"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "folder" in captured.out
    assert "doc.txt" in captured.out


def test_main_mkdir_creates_directory(tmp_path, capsys):
    exit_code = safari_dos_main(["mkdir", str(tmp_path), "Drafts"])

    captured = capsys.readouterr()
    created = tmp_path / "Drafts"
    assert exit_code == 0
    assert created.is_dir()
    assert str(created.resolve()) in captured.out


def test_main_edit_delegates_to_safari_writer(monkeypatch, tmp_path):
    document = tmp_path / "draft.sfw"
    document.write_text("Hello", encoding="utf-8")
    launched: list[list[str]] = []
    safari_writer_main_module = importlib.import_module("safari_writer.main")

    monkeypatch.setattr(
        safari_writer_main_module,
        "main",
        lambda argv: launched.append(argv) or 0,
    )

    exit_code = safari_dos_main(["edit", str(document)])

    assert exit_code == 0
    assert launched == [["tui", "edit", "--file", str(document.resolve())]]


def test_dos_help_screen_is_modal():
    """Safari DOS help screen is a ModalScreen with full key reference."""
    from safari_dos.screens import SafariDosHelpScreen, DOS_HELP_CONTENT

    screen = SafariDosHelpScreen()
    assert isinstance(screen, SafariDosHelpScreen)
    assert "FILE BROWSER" in DOS_HELP_CONTENT
    assert "MAIN MENU" in DOS_HELP_CONTENT
    assert "Ctrl+Q" in DOS_HELP_CONTENT


def test_dos_browser_has_f1_binding():
    """The browser screen has an F1 binding for help."""
    binding_keys = [b.key for b in SafariDosBrowserScreen.BINDINGS]
    assert "f1" in binding_keys


# ---------------------------------------------------------------------------
# get_preview_text
# ---------------------------------------------------------------------------


def test_get_preview_text_returns_file_contents(tmp_path):
    doc = tmp_path / "story.txt"
    doc.write_text("line one\nline two\nline three", encoding="utf-8")

    preview = get_preview_text(doc)

    assert preview == "line one\nline two\nline three"


def test_get_preview_text_limits_lines(tmp_path):
    doc = tmp_path / "long.txt"
    doc.write_text("\n".join(str(i) for i in range(100)), encoding="utf-8")

    preview = get_preview_text(doc, limit_lines=5)

    assert preview == "0\n1\n2\n3\n4"


def test_get_preview_text_returns_empty_for_directory(tmp_path):
    folder = tmp_path / "subfolder"
    folder.mkdir()

    assert get_preview_text(folder) == ""


def test_get_preview_text_returns_empty_for_missing_file(tmp_path):
    assert get_preview_text(tmp_path / "ghost.txt") == ""


def test_get_preview_text_unreadable_file_returns_error_string(tmp_path):
    """A file that raises PermissionError on open returns an error string, not an exception."""
    import sys

    doc = tmp_path / "locked.txt"
    doc.write_text("secret", encoding="utf-8")

    if sys.platform == "win32":
        # chmod is unreliable on Windows; patch Path.open instead
        with mock.patch.object(type(doc), "open", side_effect=PermissionError("Access denied")):
            result = get_preview_text(doc)
    else:
        doc.chmod(0o000)
        try:
            result = get_preview_text(doc)
        finally:
            doc.chmod(0o644)

    assert result.startswith("Error reading preview:")


# ---------------------------------------------------------------------------
# list_directory – permission-denied folder
# ---------------------------------------------------------------------------


def test_list_directory_raises_for_missing_path(tmp_path):
    import pytest

    with pytest.raises(FileNotFoundError):
        list_directory(tmp_path / "nonexistent")


def test_list_directory_raises_for_file_not_dir(tmp_path):
    import pytest

    f = tmp_path / "file.txt"
    f.write_text("hi", encoding="utf-8")

    with pytest.raises(NotADirectoryError):
        list_directory(f)


def test_list_directory_raises_for_bad_sort_field(tmp_path):
    import pytest

    with pytest.raises(ValueError, match="Unsupported sort field"):
        list_directory(tmp_path, sort_field="invalid")


def test_list_directory_filter_text(tmp_path):
    (tmp_path / "alpha.txt").write_text("a", encoding="utf-8")
    (tmp_path / "beta.txt").write_text("b", encoding="utf-8")
    (tmp_path / "gamma.txt").write_text("g", encoding="utf-8")

    entries = list_directory(tmp_path, filter_text="bet")

    assert [e.name for e in entries] == ["beta.txt"]


def test_list_directory_sort_by_date(tmp_path):
    import time

    old = tmp_path / "old.txt"
    old.write_text("old", encoding="utf-8")
    time.sleep(0.01)
    new = tmp_path / "new.txt"
    new.write_text("new", encoding="utf-8")

    entries = list_directory(tmp_path, sort_field="date")
    # date sort is newest first
    assert entries[0].name == "new.txt"
    assert entries[1].name == "old.txt"


def test_list_directory_ascending_false_reverses_within_dirs_and_files(tmp_path):
    (tmp_path / "alpha.txt").write_text("a", encoding="utf-8")
    (tmp_path / "beta.txt").write_text("b", encoding="utf-8")
    sub = tmp_path / "zdir"
    sub.mkdir()

    entries = list_directory(tmp_path, ascending=False)
    names = [e.name for e in entries]
    # dirs still come first, but reversed among themselves; then files reversed
    assert names.index("zdir") < names.index("beta.txt")
    assert names.index("beta.txt") < names.index("alpha.txt")


# ---------------------------------------------------------------------------
# get_entry_info
# ---------------------------------------------------------------------------


def test_get_entry_info_file(tmp_path):
    doc = tmp_path / "report.txt"
    doc.write_text("data", encoding="utf-8")

    info = get_entry_info(doc)

    assert "Name: report.txt" in info
    assert "Type: File" in info
    assert "Size:" in info


def test_get_entry_info_directory(tmp_path):
    folder = tmp_path / "docs"
    folder.mkdir()
    (folder / "a.txt").write_text("hi", encoding="utf-8")

    info = get_entry_info(folder)

    assert "Type: Folder" in info
    assert "Items: 1" in info


def test_get_entry_info_raises_for_missing(tmp_path):
    import pytest

    with pytest.raises(FileNotFoundError):
        get_entry_info(tmp_path / "ghost.txt")


# ---------------------------------------------------------------------------
# copy_paths / move_paths
# ---------------------------------------------------------------------------


def test_copy_paths_copies_files(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    dst = tmp_path / "dst"
    dst.mkdir()
    f = src / "note.txt"
    f.write_text("hello", encoding="utf-8")

    copied = copy_paths([f], dst)

    assert len(copied) == 1
    assert copied[0].read_text(encoding="utf-8") == "hello"
    assert f.exists()  # original untouched


def test_copy_paths_raises_when_destination_exists(tmp_path):
    import pytest

    src = tmp_path / "src"
    src.mkdir()
    dst = tmp_path / "dst"
    dst.mkdir()
    f = src / "clash.txt"
    f.write_text("a", encoding="utf-8")
    (dst / "clash.txt").write_text("b", encoding="utf-8")

    with pytest.raises(FileExistsError):
        copy_paths([f], dst)


def test_copy_paths_raises_for_non_directory_destination(tmp_path):
    import pytest

    f = tmp_path / "file.txt"
    f.write_text("x", encoding="utf-8")
    not_a_dir = tmp_path / "target.txt"
    not_a_dir.write_text("y", encoding="utf-8")

    with pytest.raises(NotADirectoryError):
        copy_paths([f], not_a_dir)


def test_move_paths_moves_files(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    dst = tmp_path / "dst"
    dst.mkdir()
    f = src / "doc.txt"
    f.write_text("content", encoding="utf-8")

    moved = move_paths([f], dst)

    assert len(moved) == 1
    assert moved[0].read_text(encoding="utf-8") == "content"
    assert not f.exists()


def test_move_paths_raises_when_destination_exists(tmp_path):
    import pytest

    src = tmp_path / "src"
    src.mkdir()
    dst = tmp_path / "dst"
    dst.mkdir()
    f = src / "clash.txt"
    f.write_text("a", encoding="utf-8")
    (dst / "clash.txt").write_text("b", encoding="utf-8")

    with pytest.raises(FileExistsError):
        move_paths([f], dst)


# ---------------------------------------------------------------------------
# zip_paths / unzip_path
# ---------------------------------------------------------------------------


def test_zip_and_unzip_round_trip(tmp_path):
    src = tmp_path / "data.txt"
    src.write_text("payload", encoding="utf-8")
    archive = tmp_path / "archive.zip"
    extract_dir = tmp_path / "out"
    extract_dir.mkdir()

    zip_paths([src], archive)
    unzip_path(archive, extract_dir)

    assert (extract_dir / "data.txt").read_text(encoding="utf-8") == "payload"


def test_zip_adds_zip_extension_when_missing(tmp_path):
    src = tmp_path / "note.txt"
    src.write_text("hi", encoding="utf-8")
    archive_no_ext = tmp_path / "bundle"

    result = zip_paths([src], archive_no_ext)

    assert result.suffix == ".zip"
    assert result.exists()


def test_unzip_raises_for_missing_archive(tmp_path):
    import pytest

    with pytest.raises(FileNotFoundError):
        unzip_path(tmp_path / "missing.zip", tmp_path)


def test_unzip_raises_for_invalid_zip(tmp_path):
    import pytest

    bad = tmp_path / "bad.zip"
    bad.write_text("not a zip", encoding="utf-8")

    with pytest.raises(ValueError, match="Not a valid ZIP file"):
        unzip_path(bad, tmp_path)


# ---------------------------------------------------------------------------
# rename_path edge cases
# ---------------------------------------------------------------------------


def test_rename_path_raises_for_empty_name(tmp_path):
    import pytest

    f = tmp_path / "draft.txt"
    f.write_text("x", encoding="utf-8")

    with pytest.raises(ValueError, match="empty"):
        rename_path(f, "   ")


def test_rename_path_raises_when_target_exists(tmp_path):
    import pytest

    f = tmp_path / "a.txt"
    f.write_text("a", encoding="utf-8")
    (tmp_path / "b.txt").write_text("b", encoding="utf-8")

    with pytest.raises(FileExistsError):
        rename_path(f, "b.txt")


# ---------------------------------------------------------------------------
# create_folder edge cases
# ---------------------------------------------------------------------------


def test_create_folder_raises_for_empty_name(tmp_path):
    import pytest

    with pytest.raises(ValueError, match="empty"):
        create_folder(tmp_path, "   ")


def test_create_folder_raises_when_folder_exists(tmp_path):
    import pytest

    (tmp_path / "existing").mkdir()

    with pytest.raises(FileExistsError):
        create_folder(tmp_path, "existing")


# ---------------------------------------------------------------------------
# duplicate_path – directory
# ---------------------------------------------------------------------------


def test_duplicate_path_copies_directory(tmp_path):
    src = tmp_path / "chapter"
    src.mkdir()
    (src / "page.txt").write_text("words", encoding="utf-8")

    dup = duplicate_path(src)

    assert dup.name == "chapter COPY"
    assert (dup / "page.txt").read_text(encoding="utf-8") == "words"
    assert src.exists()


def test_duplicate_path_increments_index_on_conflict(tmp_path):
    src = tmp_path / "note.txt"
    src.write_text("a", encoding="utf-8")
    (tmp_path / "note COPY.txt").write_text("already", encoding="utf-8")

    dup = duplicate_path(src)

    assert dup.name == "note COPY 2.txt"




# ---------------------------------------------------------------------------
# discover_locations
# ---------------------------------------------------------------------------


def test_discover_locations_includes_home():
    locations = discover_locations()
    labels = [loc.label for loc in locations]
    assert "Home" in labels


def test_discover_locations_current_path_adds_current_drive(tmp_path):
    locations = discover_locations(current_path=tmp_path)
    labels = [loc.label for loc in locations]
    assert "Current Drive" in labels


def test_discover_locations_no_duplicates(tmp_path):
    locations = discover_locations(current_path=tmp_path)
    paths = [loc.path for loc in locations]
    assert len(paths) == len(set(paths))
