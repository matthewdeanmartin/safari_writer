"""Tests for Safari Base."""

from __future__ import annotations

import asyncio

from textual.widgets import Static

import safari_base
from safari_base.app import SafariBaseApp
from safari_base.database import (DEFAULT_ADDRESS_SCHEMA, ensure_database,
                                  list_tables)
from safari_base.main import main as safari_base_main
from safari_base.main import parse_args
from safari_base.screen import (SCREEN_CSS, SafariBaseScreen,
                                clamp_shell_dimension)


def test_public_exports_are_explicit():
    expected = {
        "BaseSession",
        "DEFAULT_ADDRESS_SCHEMA",
        "SafariBaseApp",
        "build_parser",
        "ensure_database",
        "list_tables",
        "main",
        "parse_args",
    }

    assert expected.issubset(set(safari_base.__all__))


def test_parse_args_supports_optional_database():
    args = parse_args(["contacts.sqlite"])

    assert args.database == "contacts.sqlite"


def test_ensure_database_bootstraps_default_address_table(tmp_path):
    database_path = tmp_path / "contacts.sqlite"

    session = ensure_database(database_path)

    assert session.current_table == "ADDRESS"
    assert list_tables(session.connection) == ["ADDRESS"]
    assert [
        name for name, _width in DEFAULT_ADDRESS_SCHEMA
    ] == session.current_columns()


def test_append_record_persists_values(tmp_path):
    session = ensure_database(tmp_path / "contacts.sqlite")

    rowid = session.append_record(["A"] * len(session.current_columns()))

    assert rowid == 1
    row = session.browse_rows(limit=1, offset=0)[0]
    assert row[1][0] == "A"


def test_main_accepts_optional_database(monkeypatch, tmp_path):
    launched = []

    def fake_run(self) -> None:
        launched.append(self.session.database_path)

    monkeypatch.setattr(SafariBaseApp, "run", fake_run)

    exit_code = safari_base_main([str(tmp_path / "contacts.sqlite")])

    assert exit_code == 0
    assert launched == [(tmp_path / "contacts.sqlite").resolve()]


def test_default_mount_opens_address_browse():
    async def run() -> None:
        app = SafariBaseApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            screen = app.screen
            assert isinstance(screen, SafariBaseScreen)
            assert (
                "Table: ADDRESS" in screen.query_one("#workspace-title", Static).content
            )
            assert "LAST" in screen.query_one("#workspace-body", Static).content
            assert ". " == screen.query_one("#prompt-line", Static).content
            assert "Fld LAST 1/15" in screen.query_one("#status-bar", Static).content

    asyncio.run(run())


def test_set_current_table_is_case_insensitive(tmp_path):
    session = ensure_database(tmp_path / "contacts.sqlite")

    session.set_current_table("address")

    assert session.current_table == "ADDRESS"


def test_arrow_key_does_not_crash_prompt_handling():
    async def run() -> None:
        app = SafariBaseApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            await pilot.press("right")
            screen = app.screen
            assert isinstance(screen, SafariBaseScreen)
            assert ". " == screen.query_one("#prompt-line", Static).content
            assert "Fld FIRST 2/15" in screen.query_one("#status-bar", Static).content

    asyncio.run(run())


def test_screen_css_uses_roomier_shell():
    assert "width: 100;" in SCREEN_CSS
    assert "height: 34;" in SCREEN_CSS
    assert "#prompt-line" in SCREEN_CSS
    assert "#button-bar" not in SCREEN_CSS


def test_shell_dimension_clamps_to_terminal_size():
    assert clamp_shell_dimension(120, 80) == 80
    assert clamp_shell_dimension(40, 80) == 40
    assert clamp_shell_dimension(0, 60) == 1


def test_function_keys_are_wired():
    async def run() -> None:
        app = SafariBaseApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            await pilot.press("f10")
            screen = app.screen
            assert isinstance(screen, SafariBaseScreen)
            assert "ASSIST" in screen.query_one("#status-bar", Static).content
            # ASSIST menu should show categories in the workspace
            assert "Set Up" in screen.query_one("#workspace-body", Static).content
            await pilot.press("escape")  # dismiss ASSIST
            await pilot.press("f2")
            assert "ASSIST" in screen.query_one("#status-bar", Static).content
            await pilot.press("escape")  # dismiss ASSIST from f2
            await pilot.press("f6")
            assert (
                "Field      Type" in screen.query_one("#workspace-body", Static).content
            )
            await pilot.press("f7")
            assert (
                "Available tables"
                in screen.query_one("#workspace-body", Static).content
            )
            await pilot.press("f8")
            assert "LAST" in screen.query_one("#workspace-body", Static).content

    asyncio.run(run())


def test_ctrl_a_shows_placeholder_and_prompt_still_updates():
    async def run() -> None:
        app = SafariBaseApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            await pilot.press("ctrl+a", "x", "y", "z")
            screen = app.screen
            assert isinstance(screen, SafariBaseScreen)
            assert (
                "Append form active" in screen.query_one("#status-bar", Static).content
            )
            assert "> LAST" in screen.query_one("#workspace-body", Static).content
            assert "xyz" in screen.query_one("#workspace-body", Static).content

    asyncio.run(run())


def test_prompt_supports_cursor_navigation_and_editing():
    async def run() -> None:
        app = SafariBaseApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            await pilot.press("a", "b", "c", "left", "left", "delete")
            prompt = app.screen.query_one("#prompt-line", Static).content
            assert prompt == ". ac"

    asyncio.run(run())


def test_browse_tab_navigation_updates_focus():
    async def run() -> None:
        app = SafariBaseApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            await pilot.press("tab")
            status = app.screen.query_one("#status-bar", Static).content
            body = app.screen.query_one("#workspace-body", Static).content
            assert "Fld FIRST 2/15" in status
            assert "[FIRST" in body

    asyncio.run(run())


def test_insert_and_caps_toggles_update_scoreboard():
    async def run() -> None:
        app = SafariBaseApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            await pilot.press("insert", "f9", "x")
            scoreboard = app.screen.query_one("#scoreboard", Static).content
            prompt = app.screen.query_one("#prompt-line", Static).content
            assert "Ins OFF" in scoreboard
            assert "Caps ON" in scoreboard
            assert prompt == ". X"

    asyncio.run(run())


def test_append_form_saves_record():
    async def run() -> None:
        app = SafariBaseApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            await pilot.press("f3", "S", "m", "i", "t", "h", "enter", "J", "o", "enter")
            await pilot.press("ctrl+s")
            screen = app.screen
            assert isinstance(screen, SafariBaseScreen)
            assert "Saved record" in screen.query_one("#status-bar", Static).content
            assert "Smith" in screen.query_one("#workspace-body", Static).content

    asyncio.run(run())


def test_ctrl_d_uses_delete_placeholder_message():
    async def run() -> None:
        app = SafariBaseApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            await pilot.press("ctrl+d")
            assert (
                "Delete mark not implemented yet"
                in app.screen.query_one(
                    "#status-bar",
                    Static,
                ).content
            )

    asyncio.run(run())


def test_command_abbreviations_and_reports_work():
    async def run() -> None:
        app = SafariBaseApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            await pilot.press("l", "i", "s", "t", "enter")
            title = app.screen.query_one("#workspace-title", Static).content
            body = app.screen.query_one("#workspace-body", Static).content
            assert "LIST" in title
            assert "LIST ADDRESS" in body

            await pilot.press("c", "o", "m", "m", "enter")
            assert (
                "Supported commands"
                in app.screen.query_one("#workspace-body", Static).content
            )

            await pilot.press("b", "r", "o", "w", "enter")
            assert "LAST" in app.screen.query_one("#workspace-body", Static).content

    asyncio.run(run())


def test_bridge_mail_merge_to_session_roundtrip():
    from safari_base.bridge import mail_merge_to_session, session_to_mail_merge
    from safari_writer.mail_merge_db import FieldDef, MailMergeDB

    db = MailMergeDB(
        fields=[FieldDef("Last Name", 20), FieldDef("First Name", 20)],
        records=[["Smith", "John"], ["Doe", "Jane"]],
        filename="test.json",
    )

    session = mail_merge_to_session(db)
    assert session.record_count() == 2
    assert session.current_columns()[:2] == ["LAST", "FIRST"]

    roundtrip = session_to_mail_merge(session, original=db)
    assert len(roundtrip.fields) == 2
    assert roundtrip.fields[0].name == "Last Name"
    assert roundtrip.fields[1].name == "First Name"
    assert len(roundtrip.records) == 2
    assert roundtrip.records[0] == ["Smith", "John"]
    assert roundtrip.records[1] == ["Doe", "Jane"]
    assert roundtrip.filename == "test.json"


def test_bridge_session_to_mail_merge_without_original():
    from safari_base.bridge import mail_merge_to_session, session_to_mail_merge
    from safari_writer.mail_merge_db import FieldDef, MailMergeDB

    db = MailMergeDB(
        fields=[FieldDef("Last Name", 20), FieldDef("First Name", 20)],
        records=[["Alpha", "Beta"]],
    )
    session = mail_merge_to_session(db)
    result = session_to_mail_merge(session, original=None)
    assert result.fields[0].name == "LAST"
    assert result.fields[1].name == "FIRST"
    assert result.records == [["Alpha", "Beta"]]


def test_bridge_append_in_session_reflects_in_roundtrip():
    from safari_base.bridge import mail_merge_to_session, session_to_mail_merge
    from safari_writer.mail_merge_db import FieldDef, MailMergeDB

    db = MailMergeDB(
        fields=[FieldDef("Last Name", 20), FieldDef("First Name", 20)],
        records=[],
    )
    session = mail_merge_to_session(db)
    session.append_record(["New", "Person"])
    result = session_to_mail_merge(session, original=db)
    assert len(result.records) == 1
    assert result.records[0] == ["New", "Person"]


def test_assist_menu_navigation():
    async def run() -> None:
        app = SafariBaseApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            await pilot.press("f10")
            screen = app.screen
            assert isinstance(screen, SafariBaseScreen)
            body = screen.query_one("#workspace-body", Static).content
            assert "Set Up" in body
            assert "Browse" in body

            # Navigate right to "Update" category
            await pilot.press("right")
            body = screen.query_one("#workspace-body", Static).content
            assert "Append" in body

            # Select Append via Enter
            await pilot.press("enter")
            assert screen._view_mode == "append"

    asyncio.run(run())


def test_do_command_in_screen(tmp_path):
    async def run() -> None:
        prg_path = tmp_path / "hello.prg"
        prg_path.write_text('? "HELLO FROM PRG"')

        # We need to ensure SafariBaseApp uses tmp_path as its working directory
        # but SafariBaseApp(database_path=...) might be easier
        db_path = tmp_path / "test.sqlite"
        app = SafariBaseApp(database_path=db_path)

        async with app.run_test() as pilot:
            await pilot.pause()
            # Type "DO hello" and press enter
            # We use f9 to ensure caps off if needed, but let's just type
            for char in "do hello":
                await pilot.press(char)
            await pilot.press("enter")
            await pilot.pause()

            screen = app.screen
            assert isinstance(screen, SafariBaseScreen)
            title = screen.query_one("#workspace-title", Static).content
            body = screen.query_one("#workspace-body", Static).content

            assert "DO hello.prg" in title
            assert "HELLO FROM PRG" in body

    asyncio.run(run())
