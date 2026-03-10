"""Exercise script for the Program Editor screen.

Tests the ProgramEditorScreen in headless mode to verify:
- File loading
- Text insertion / editing
- Line splitting (Enter)
- Backspace / delete
- Line deletion (Ctrl+Y)
- Save / load round-trip
- New file creation
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from safari_base.program_editor import ProgramEditorScreen


def test_load_existing_file() -> None:
    """Test loading an existing .prg file."""
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
        prg = Path(tmpdir) / "test.prg"
        prg.write_text("USE CUSTOMER\nGO TOP\n? NAME\nRETURN\n", encoding="utf-8")

        editor = ProgramEditorScreen(prg)
        assert len(editor._lines) == 4, f"Expected 4 lines, got {len(editor._lines)}"
        assert editor._lines[0] == "USE CUSTOMER"
        assert editor._lines[1] == "GO TOP"
        assert editor._lines[2] == "? NAME"
        assert editor._lines[3] == "RETURN"
        assert not editor._dirty
        print("  OK  load existing file")


def test_new_file() -> None:
    """Test creating a new file."""
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
        prg = Path(tmpdir) / "new.prg"
        editor = ProgramEditorScreen(prg)
        assert len(editor._lines) == 1
        assert editor._lines[0] == ""
        assert not editor._dirty
        print("  OK  new file starts with one empty line")


def test_insert_text() -> None:
    """Test inserting text."""
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
        prg = Path(tmpdir) / "test.prg"
        editor = ProgramEditorScreen(prg)

        # Insert text character by character
        for ch in "USE CUSTOMER":
            editor._insert_text(ch)

        assert editor._lines[0] == "USE CUSTOMER"
        assert editor._cursor_col == 12
        assert editor._dirty
        print("  OK  insert text")


def test_split_line() -> None:
    """Test splitting a line with Enter."""
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
        prg = Path(tmpdir) / "test.prg"
        prg.write_text("USE CUSTOMERGO TOP\n", encoding="utf-8")
        editor = ProgramEditorScreen(prg)

        # Position cursor at column 12 and split
        editor._cursor_col = 12
        editor._split_line()

        assert len(editor._lines) == 2
        assert editor._lines[0] == "USE CUSTOMER"
        assert editor._lines[1] == "GO TOP"
        assert editor._cursor_line == 1
        assert editor._cursor_col == 0
        print("  OK  split line")


def test_backspace() -> None:
    """Test backspace within a line and joining lines."""
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
        prg = Path(tmpdir) / "test.prg"
        prg.write_text("ABCDEF\n", encoding="utf-8")
        editor = ProgramEditorScreen(prg)

        # Backspace in middle of line
        editor._cursor_col = 3
        editor._backspace()
        assert editor._lines[0] == "ABDEF"
        assert editor._cursor_col == 2

        # Reset
        prg.write_text("LINE1\nLINE2\n", encoding="utf-8")
        editor._load_file()

        # Backspace at start of line 2 joins with line 1
        editor._cursor_line = 1
        editor._cursor_col = 0
        editor._backspace()
        assert len(editor._lines) == 1
        assert editor._lines[0] == "LINE1LINE2"
        assert editor._cursor_col == 5
        print("  OK  backspace")


def test_delete_char() -> None:
    """Test delete key."""
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
        prg = Path(tmpdir) / "test.prg"
        prg.write_text("ABCDEF\n", encoding="utf-8")
        editor = ProgramEditorScreen(prg)

        editor._cursor_col = 2
        editor._delete_char()
        assert editor._lines[0] == "ABDEF"

        # Delete at end of line joins with next
        prg.write_text("LINE1\nLINE2\n", encoding="utf-8")
        editor._load_file()
        editor._cursor_col = 5
        editor._delete_char()
        assert len(editor._lines) == 1
        assert editor._lines[0] == "LINE1LINE2"
        print("  OK  delete char")


def test_delete_line() -> None:
    """Test Ctrl+Y to delete entire line."""
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
        prg = Path(tmpdir) / "test.prg"
        prg.write_text("LINE1\nLINE2\nLINE3\n", encoding="utf-8")
        editor = ProgramEditorScreen(prg)

        editor._cursor_line = 1
        editor._delete_line()
        assert len(editor._lines) == 2
        assert editor._lines[0] == "LINE1"
        assert editor._lines[1] == "LINE3"

        # Delete last remaining line leaves one empty
        editor._lines = ["ONLY"]
        editor._cursor_line = 0
        editor._delete_line()
        assert len(editor._lines) == 1
        assert editor._lines[0] == ""
        print("  OK  delete line")


def test_delete_to_eol() -> None:
    """Test Ctrl+K to delete to end of line."""
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
        prg = Path(tmpdir) / "test.prg"
        prg.write_text("USE CUSTOMER\n", encoding="utf-8")
        editor = ProgramEditorScreen(prg)

        editor._cursor_col = 4
        editor._delete_to_eol()
        assert editor._lines[0] == "USE "
        print("  OK  delete to EOL")


def test_save_roundtrip() -> None:
    """Test save and reload."""
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
        prg = Path(tmpdir) / "roundtrip.prg"
        editor = ProgramEditorScreen(prg)

        # Write some content
        editor._lines = [
            "* My Report Program",
            "USE CUSTOMER",
            "GO TOP",
            "DO WHILE .NOT. EOF()",
            "    ? NAME, BALANCE",
            "    SKIP",
            "ENDDO",
            "RETURN",
        ]
        editor._dirty = True
        editor._save_file()

        assert prg.exists()
        assert not editor._dirty

        # Reload and verify
        editor2 = ProgramEditorScreen(prg)
        assert len(editor2._lines) == 8
        assert editor2._lines[0] == "* My Report Program"
        assert editor2._lines[3] == "DO WHILE .NOT. EOF()"
        assert editor2._lines[7] == "RETURN"
        print("  OK  save/load roundtrip")


def test_overwrite_mode() -> None:
    """Test overwrite (non-insert) mode."""
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
        prg = Path(tmpdir) / "test.prg"
        prg.write_text("ABCDEF\n", encoding="utf-8")
        editor = ProgramEditorScreen(prg)

        editor._insert_mode = False
        editor._cursor_col = 2
        editor._insert_text("X")
        assert editor._lines[0] == "ABXDEF"  # Wait, insert=False means overwrite
        # Actually in overwrite mode, C should be replaced
        # Let me re-check the logic...

        # Reset and test properly
        editor._load_file()
        editor._insert_mode = False
        editor._cursor_col = 2
        editor._insert_text("X")
        # Should replace 'C' with 'X': "ABXDEF"
        assert editor._lines[0] == "ABXDEF", f"Got: {editor._lines[0]}"
        print("  OK  overwrite mode")


def test_navigation() -> None:
    """Test cursor movement."""
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
        prg = Path(tmpdir) / "test.prg"
        prg.write_text("SHORT\nA LONGER LINE HERE\nEND\n", encoding="utf-8")
        editor = ProgramEditorScreen(prg)

        # Move down
        editor._move_down()
        assert editor._cursor_line == 1

        # Move to end of long line
        editor._cursor_col = 18
        # Move down to shorter line — col should clamp
        editor._move_down()
        assert editor._cursor_line == 2
        assert editor._cursor_col == 3  # "END" is 3 chars

        # Move up
        editor._move_up()
        assert editor._cursor_line == 1
        assert editor._cursor_col == 3  # stays at clamped col? No, clamp_col re-checks

        # Left wraps to previous line
        editor._cursor_line = 1
        editor._cursor_col = 0
        editor._move_left()
        assert editor._cursor_line == 0
        assert editor._cursor_col == 5  # end of "SHORT"

        # Right wraps to next line
        editor._cursor_col = 5  # end of "SHORT"
        editor._move_right()
        assert editor._cursor_line == 1
        assert editor._cursor_col == 0
        print("  OK  navigation")


def main() -> int:
    print("=== Program Editor Tests ===\n")
    test_load_existing_file()
    test_new_file()
    test_insert_text()
    test_split_line()
    test_backspace()
    test_delete_char()
    test_delete_line()
    test_delete_to_eol()
    test_save_roundtrip()
    test_overwrite_mode()
    test_navigation()
    print("\n=== ALL PROGRAM EDITOR TESTS PASSED ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
