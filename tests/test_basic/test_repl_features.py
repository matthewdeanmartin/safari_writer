"""Tests for Safari Basic REPL extension features.

Covers: EDIT, DELETE, dirty state, FILES/DIR, PWD/CD, FIND, REPLACE,
TRON VARS, tab completion, better error reporting, AUTOSAVE, HELP <topic>,
and persistent history.
"""
import io
import os
import tempfile
import time
import pytest
from safari_basic.repl import SafariREPL, HELP_TOPICS, BASIC_KEYWORDS
from safari_basic.interpreter import SafariBasic, BasicError


def make_repl() -> tuple[SafariREPL, io.StringIO]:
    """Create a REPL with captured output."""
    out = io.StringIO()
    repl = SafariREPL(out_stream=out)
    return repl, out


def output(out: io.StringIO) -> str:
    return out.getvalue()


def reset_output(out: io.StringIO):
    out.truncate(0)
    out.seek(0)


# ─── EDIT ────────────────────────────────────────────────────────────────


class TestEdit:
    def test_edit_shows_line(self):
        repl, out = make_repl()
        repl.process_line('10 PRINT "HELLO"')
        reset_output(out)
        repl.process_line("EDIT 10")
        assert '10 PRINT "HELLO"' in output(out)

    def test_edit_nonexistent_line(self):
        repl, out = make_repl()
        repl.process_line("EDIT 99")
        assert "NOT FOUND" in output(out)

    def test_edit_no_argument(self):
        repl, out = make_repl()
        repl.process_line("EDIT")
        assert "REQUIRES" in output(out)

    def test_edit_non_numeric(self):
        repl, out = make_repl()
        repl.process_line("EDIT ABC")
        assert "REQUIRES" in output(out)


# ─── DELETE ──────────────────────────────────────────────────────────────


class TestDelete:
    def test_delete_single_line(self):
        repl, out = make_repl()
        repl.process_line('10 PRINT "A"')
        repl.process_line('20 PRINT "B"')
        reset_output(out)
        repl.process_line("DELETE 10")
        assert "DELETED 1 LINE" in output(out)
        assert 10 not in repl.interpreter.lines
        assert 20 in repl.interpreter.lines

    def test_delete_range(self):
        repl, out = make_repl()
        repl.process_line('10 PRINT "A"')
        repl.process_line('20 PRINT "B"')
        repl.process_line('30 PRINT "C"')
        reset_output(out)
        repl.process_line("DELETE 10,20")
        assert "DELETED 2 LINES" in output(out)
        assert 10 not in repl.interpreter.lines
        assert 20 not in repl.interpreter.lines
        assert 30 in repl.interpreter.lines

    def test_delete_no_lines_in_range(self):
        repl, out = make_repl()
        repl.process_line('10 PRINT "A"')
        reset_output(out)
        repl.process_line("DELETE 50,100")
        assert "NO LINES IN RANGE" in output(out)

    def test_delete_sets_modified(self):
        repl, out = make_repl()
        repl.process_line('10 PRINT "A"')
        repl.modified = False
        repl.process_line("DELETE 10")
        assert repl.modified is True

    def test_delete_supports_undo(self):
        repl, out = make_repl()
        repl.process_line('10 PRINT "A"')
        repl.process_line('20 PRINT "B"')
        repl.process_line("DELETE 10,20")
        assert len(repl.interpreter.lines) == 0
        repl.process_line("UNDO")
        assert 10 in repl.interpreter.lines
        assert 20 in repl.interpreter.lines

    def test_delete_no_argument(self):
        repl, out = make_repl()
        repl.process_line("DELETE")
        assert "REQUIRES" in output(out)


# ─── DIRTY STATE TRACKING ───────────────────────────────────────────────


class TestDirtyState:
    def test_new_program_not_modified(self):
        repl, out = make_repl()
        assert repl.modified is False

    def test_adding_line_sets_modified(self):
        repl, out = make_repl()
        repl.process_line('10 PRINT "HI"')
        assert repl.modified is True

    def test_save_clears_modified(self):
        repl, out = make_repl()
        repl.process_line('10 PRINT "HI"')
        with tempfile.NamedTemporaryFile(suffix=".bas", delete=False) as f:
            fname = f.name
        try:
            repl.process_line(f'SAVE "{fname}"')
            assert repl.modified is False
        finally:
            os.unlink(fname)

    def test_load_clears_modified(self):
        repl, out = make_repl()
        with tempfile.NamedTemporaryFile(mode='w', suffix=".bas", delete=False) as f:
            f.write('10 PRINT "HI"\n')
            fname = f.name
        try:
            repl.process_line('20 PRINT "DIRTY"')
            assert repl.modified is True
            repl.process_line(f'LOAD "{fname}"')
            assert repl.modified is False
        finally:
            os.unlink(fname)

    def test_new_warns_unsaved(self):
        repl, out = make_repl()
        repl.process_line('10 PRINT "HI"')
        reset_output(out)
        repl.process_line("NEW")
        assert "WARNING" in output(out) or "UNSAVED" in output(out)

    def test_load_warns_unsaved(self):
        repl, out = make_repl()
        repl.process_line('10 PRINT "HI"')
        reset_output(out)
        with tempfile.NamedTemporaryFile(mode='w', suffix=".bas", delete=False) as f:
            f.write('10 PRINT "OTHER"\n')
            fname = f.name
        try:
            repl.process_line(f'LOAD "{fname}"')
            assert "WARNING" in output(out) or "UNSAVED" in output(out)
        finally:
            os.unlink(fname)

    def test_exit_warns_unsaved(self):
        repl, out = make_repl()
        repl.process_line('10 PRINT "HI"')
        reset_output(out)
        result = repl.process_line("EXIT")
        assert result is False
        assert "WARNING" in output(out) or "UNSAVED" in output(out)


# ─── FILES / DIR ─────────────────────────────────────────────────────────


class TestFilesDir:
    def test_files_lists_directory(self):
        repl, out = make_repl()
        old_dir = os.getcwd()
        with tempfile.TemporaryDirectory() as tmpdir:
            os.chdir(tmpdir)
            try:
                with open("test.bas", "w") as f:
                    f.write("10 PRINT 1\n")
                repl.process_line("FILES")
                result = output(out)
                assert "test.bas" in result
                assert "1 FILE" in result
            finally:
                os.chdir(old_dir)

    def test_files_with_pattern(self):
        repl, out = make_repl()
        old_dir = os.getcwd()
        with tempfile.TemporaryDirectory() as tmpdir:
            os.chdir(tmpdir)
            try:
                with open("test.bas", "w") as f:
                    f.write("10 PRINT 1\n")
                with open("readme.txt", "w") as f:
                    f.write("hello\n")
                repl.process_line("FILES *.bas")
                result = output(out)
                assert "test.bas" in result
                assert "readme.txt" not in result
            finally:
                os.chdir(old_dir)

    def test_dir_alias(self):
        repl, out = make_repl()
        old_dir = os.getcwd()
        with tempfile.TemporaryDirectory() as tmpdir:
            os.chdir(tmpdir)
            try:
                with open("test.bas", "w") as f:
                    f.write("10 PRINT 1\n")
                repl.process_line("DIR")
                assert "test.bas" in output(out)
            finally:
                os.chdir(old_dir)

    def test_files_shows_dirs(self):
        repl, out = make_repl()
        old_dir = os.getcwd()
        with tempfile.TemporaryDirectory() as tmpdir:
            os.chdir(tmpdir)
            os.mkdir("subdir")
            try:
                repl.process_line("FILES")
                assert "<DIR>" in output(out)
            finally:
                os.chdir(old_dir)


# ─── PWD / CD ────────────────────────────────────────────────────────────


class TestPwdCd:
    def test_pwd(self):
        repl, out = make_repl()
        repl.process_line("PWD")
        assert os.getcwd() in output(out)

    def test_cd_quoted(self):
        repl, out = make_repl()
        old_dir = os.getcwd()
        with tempfile.TemporaryDirectory() as tmpdir:
            try:
                repl.process_line(f'CD "{tmpdir}"')
                assert os.path.samefile(os.getcwd(), tmpdir)
            finally:
                os.chdir(old_dir)

    def test_cd_unquoted(self):
        repl, out = make_repl()
        old_dir = os.getcwd()
        with tempfile.TemporaryDirectory() as tmpdir:
            try:
                repl.process_line(f"CD {tmpdir}")
                assert os.path.samefile(os.getcwd(), tmpdir)
            finally:
                os.chdir(old_dir)

    def test_cd_invalid(self):
        repl, out = make_repl()
        repl.process_line('CD "/nonexistent_dir_xyz"')
        assert "ERROR" in output(out)


# ─── FIND ────────────────────────────────────────────────────────────────


class TestFind:
    def test_find_text(self):
        repl, out = make_repl()
        repl.process_line('10 PRINT "HELLO"')
        repl.process_line('20 PRINT "WORLD"')
        repl.process_line('30 PRINT "HI"')
        reset_output(out)
        repl.process_line('FIND "PRINT"')
        result = output(out)
        assert "3 LINES FOUND" in result

    def test_find_case_insensitive(self):
        repl, out = make_repl()
        repl.process_line('10 PRINT "hello"')
        reset_output(out)
        repl.process_line('FIND "HELLO"')
        assert "1 LINE FOUND" in output(out)

    def test_find_not_found(self):
        repl, out = make_repl()
        repl.process_line('10 PRINT "HELLO"')
        reset_output(out)
        repl.process_line('FIND "MISSING"')
        assert "NOT FOUND" in output(out)

    def test_find_shows_pointer(self):
        repl, out = make_repl()
        repl.process_line('10 PRINT "HELLO"')
        reset_output(out)
        repl.process_line('FIND "HELLO"')
        result = output(out)
        assert "^" in result

    def test_find_no_argument(self):
        repl, out = make_repl()
        repl.process_line('FIND')
        assert "REQUIRES" in output(out)


# ─── REPLACE ─────────────────────────────────────────────────────────────


class TestReplace:
    def test_replace_text(self):
        repl, out = make_repl()
        repl.process_line('10 PRINT "HELLO"')
        repl.process_line('20 PRINT "HELLO WORLD"')
        reset_output(out)
        repl.process_line('REPLACE "HELLO","HI"')
        result = output(out)
        assert "REPLACED IN 2 LINES" in result
        assert repl.interpreter.lines[10] == 'PRINT "HI"'
        assert repl.interpreter.lines[20] == 'PRINT "HI WORLD"'

    def test_replace_case_insensitive(self):
        repl, out = make_repl()
        repl.process_line('10 print "hello"')
        reset_output(out)
        repl.process_line('REPLACE "PRINT","??"')
        assert "REPLACED IN 1 LINE" in output(out)

    def test_replace_not_found(self):
        repl, out = make_repl()
        repl.process_line('10 PRINT "A"')
        reset_output(out)
        repl.process_line('REPLACE "XYZ","ABC"')
        assert "NOT FOUND" in output(out)

    def test_replace_sets_modified(self):
        repl, out = make_repl()
        repl.process_line('10 PRINT "A"')
        repl.modified = False
        repl.process_line('REPLACE "PRINT","?"')
        assert repl.modified is True

    def test_replace_supports_undo(self):
        repl, out = make_repl()
        repl.process_line('10 PRINT "HELLO"')
        repl.process_line('REPLACE "HELLO","BYE"')
        assert repl.interpreter.lines[10] == 'PRINT "BYE"'
        repl.process_line("UNDO")
        assert repl.interpreter.lines[10] == 'PRINT "HELLO"'

    def test_replace_no_arguments(self):
        repl, out = make_repl()
        repl.process_line('REPLACE')
        assert "REQUIRES" in output(out)


# ─── TRON VARS ───────────────────────────────────────────────────────────


class TestTronVars:
    def test_tron_vars_shows_changes(self):
        out = io.StringIO()
        interp = SafariBasic(out_stream=out)
        interp.add_program_line("10 TRON VARS")
        interp.add_program_line("20 A = 5")
        interp.add_program_line("30 A = 10")
        interp.add_program_line("40 END")
        interp.run_program()
        result = out.getvalue()
        assert "A = 5" in result
        assert "A = 10" in result

    def test_tron_vars_shows_string_changes(self):
        out = io.StringIO()
        interp = SafariBasic(out_stream=out)
        interp.add_program_line("10 TRON VARS")
        interp.add_program_line("20 DIM N$(20)")
        interp.add_program_line('30 N$ = "HELLO"')
        interp.add_program_line("40 END")
        interp.run_program()
        result = out.getvalue()
        assert 'N$ = "HELLO"' in result

    def test_troff_stops_var_tracing(self):
        out = io.StringIO()
        interp = SafariBasic(out_stream=out)
        interp.add_program_line("10 TRON VARS")
        interp.add_program_line("20 A = 1")
        interp.add_program_line("30 TROFF")
        interp.add_program_line("40 B = 2")
        interp.add_program_line("50 END")
        interp.run_program()
        result = out.getvalue()
        assert "A = 1" in result
        # B = 2 should NOT appear as traced var output (it's after TROFF)
        # It may appear as just "B = 2" in trace but not as var trace
        lines = result.strip().split("\n")
        # After TROFF, no "  B = 2" (indented var trace)
        var_trace_b = [l for l in lines if l.strip() == "B = 2" and l.startswith("  ")]
        assert len(var_trace_b) == 0

    def test_plain_tron_still_works(self):
        out = io.StringIO()
        interp = SafariBasic(out_stream=out)
        interp.add_program_line('10 TRON')
        interp.add_program_line('20 PRINT "HI"')
        interp.add_program_line('30 TROFF')
        interp.run_program()
        result = out.getvalue()
        assert "[20]" in result
        assert interp.trace_vars is False


# ─── TAB COMPLETION ──────────────────────────────────────────────────────


class TestTabCompletion:
    def test_keyword_completion(self):
        repl, out = make_repl()
        results = repl.complete("PRI")
        assert "PRINT" in results

    def test_keyword_completion_case(self):
        repl, out = make_repl()
        results = repl.complete("pri")
        assert "PRINT" in results

    def test_line_number_completion(self):
        repl, out = make_repl()
        repl.process_line('10 PRINT "A"')
        repl.process_line('20 PRINT "B"')
        repl.process_line('100 PRINT "C"')
        results = repl.complete("1")
        assert "10" in results
        assert "100" in results
        assert "20" not in results

    def test_empty_prefix(self):
        repl, out = make_repl()
        results = repl.complete("")
        # Should return all keywords
        assert len(results) >= len(BASIC_KEYWORDS)

    def test_no_match(self):
        repl, out = make_repl()
        results = repl.complete("ZZZZZ")
        # Should still return file matches potentially, but no keywords
        kw_matches = [r for r in results if r in BASIC_KEYWORDS]
        assert len(kw_matches) == 0


# ─── BETTER ERROR REPORTING ──────────────────────────────────────────────


class TestBetterErrors:
    def test_error_shows_line_number(self):
        out = io.StringIO()
        interp = SafariBasic(out_stream=out)
        interp.add_program_line("10 GOTO 999")
        try:
            interp.run_program()
        except BasicError:
            pass
        result = out.getvalue()
        assert "AT LINE 10" in result

    def test_error_descriptive_message(self):
        out = io.StringIO()
        interp = SafariBasic(out_stream=out)
        interp.add_program_line("10 X = 1 / 0")
        try:
            interp.run_program()
        except BasicError:
            pass
        result = out.getvalue()
        assert "Division by zero" in result

    def test_type_mismatch_error(self):
        out = io.StringIO()
        interp = SafariBasic(out_stream=out)
        interp.add_program_line('10 A = "HELLO" + 5')
        try:
            interp.run_program()
        except BasicError:
            pass
        result = out.getvalue()
        assert "Type mismatch" in result

    def test_undefined_line_target(self):
        out = io.StringIO()
        interp = SafariBasic(out_stream=out)
        interp.add_program_line("10 GOTO 500")
        try:
            interp.run_program()
        except BasicError:
            pass
        result = out.getvalue()
        assert "500" in result


# ─── AUTOSAVE ────────────────────────────────────────────────────────────


class TestAutosave:
    def test_autosave_requires_filename(self):
        repl, out = make_repl()
        repl.process_line("AUTOSAVE ON")
        assert "SAVE FILE FIRST" in output(out)

    def test_autosave_on_off(self):
        repl, out = make_repl()
        with tempfile.NamedTemporaryFile(suffix=".bas", delete=False) as f:
            fname = f.name
        try:
            repl.process_line('10 PRINT "HI"')
            repl.process_line(f'SAVE "{fname}"')
            reset_output(out)
            repl.process_line("AUTOSAVE ON")
            assert "AUTOSAVE ON" in output(out)
            assert repl._autosave_enabled is True
            reset_output(out)
            repl.process_line("AUTOSAVE OFF")
            assert "AUTOSAVE OFF" in output(out)
            assert repl._autosave_enabled is False
        finally:
            os.unlink(fname)

    def test_autosave_status(self):
        repl, out = make_repl()
        repl.process_line("AUTOSAVE")
        assert "OFF" in output(out)

    def test_autosave_tick_saves(self):
        repl, out = make_repl()
        with tempfile.NamedTemporaryFile(suffix=".bas", delete=False, mode='w') as f:
            fname = f.name
        try:
            repl.process_line('10 PRINT "SAVED"')
            repl.process_line(f'SAVE "{fname}"')
            repl.process_line('20 PRINT "UPDATED"')
            assert repl.modified is True
            # Simulate an autosave tick
            repl._autosave_enabled = True
            repl._do_autosave_tick()
            repl._stop_autosave()
            assert repl.modified is False
            with open(fname, 'r') as f:
                content = f.read()
            assert 'PRINT "UPDATED"' in content
        finally:
            os.unlink(fname)


# ─── HELP <TOPIC> ────────────────────────────────────────────────────────


class TestHelpTopics:
    def test_help_no_topic_lists_commands(self):
        repl, out = make_repl()
        repl.process_line("HELP")
        result = output(out)
        assert "LIST" in result
        assert "HELP <topic>" in result

    def test_help_specific_topic(self):
        repl, out = make_repl()
        repl.process_line("HELP PRINT")
        result = output(out)
        assert "Output values" in result or "PRINT" in result

    def test_help_unknown_topic(self):
        repl, out = make_repl()
        repl.process_line("HELP XYZZY")
        assert "NO HELP FOR" in output(out)

    def test_all_major_topics_exist(self):
        for topic in ["LIST", "RUN", "NEW", "LOAD", "SAVE", "EDIT", "DELETE",
                       "FIND", "REPLACE", "TRON", "TROFF", "FILES", "PWD", "CD",
                       "AUTOSAVE", "PRINT", "INPUT", "IF", "FOR", "GOTO", "GOSUB",
                       "DIM", "END", "STOP", "HELP"]:
            assert topic in HELP_TOPICS, f"Missing help topic: {topic}"


# ─── PERSISTENT HISTORY ─────────────────────────────────────────────────


class TestHistory:
    def test_history_recorded(self):
        repl, out = make_repl()
        repl.process_line('PRINT "HI"')
        repl.process_line("LIST")
        assert len(repl.history) >= 2
        assert 'PRINT "HI"' in repl.history
        assert "LIST" in repl.history

    def test_no_duplicate_history(self):
        repl, out = make_repl()
        repl.process_line("LIST")
        repl.process_line("LIST")
        count = repl.history.count("LIST")
        assert count == 1

    def test_empty_line_not_recorded(self):
        repl, out = make_repl()
        repl.history = []  # Clear any loaded history
        repl.process_line("")
        assert len(repl.history) == 0

    def test_history_save_load(self):
        repl, out = make_repl()
        old_file = repl.HISTORY_FILE
        repl.HISTORY_FILE = ".safari_test_history"
        try:
            repl.process_line('PRINT "HI"')
            repl.process_line("LIST")
            repl._save_history()

            repl2, out2 = make_repl()
            repl2.HISTORY_FILE = ".safari_test_history"
            repl2._load_history()
            assert 'PRINT "HI"' in repl2.history
            assert "LIST" in repl2.history
        finally:
            path = os.path.join(os.path.expanduser("~"), ".safari_test_history")
            if os.path.exists(path):
                os.unlink(path)


# ─── EXAMPLE FILES ───────────────────────────────────────────────────────


class TestExamples:
    def test_hello_example_loads(self):
        repl, out = make_repl()
        example = os.path.join(os.path.dirname(__file__), "..", "..", "safari_basic", "examples", "hello.bas")
        example = os.path.abspath(example)
        if os.path.exists(example):
            repl.process_line(f'LOAD "{example}"')
            assert 10 in repl.interpreter.lines
            reset_output(out)
            repl.process_line("RUN")
            assert "HELLO" in output(out)

    def test_fibonacci_example_runs(self):
        repl, out = make_repl()
        example = os.path.join(os.path.dirname(__file__), "..", "..", "safari_basic", "examples", "fibonacci.bas")
        example = os.path.abspath(example)
        if os.path.exists(example):
            repl.process_line(f'LOAD "{example}"')
            reset_output(out)
            repl.process_line("RUN")
            result = output(out)
            # Fibonacci starts 0, 1, 1, 2, 3, 5...
            assert "0" in result
            assert "1" in result

    def test_examples_command_lists(self):
        repl, out = make_repl()
        repl.process_line("EXAMPLES")
        result = output(out)
        assert "DEMO PROGRAMS:" in result
        assert "HELLO" in result
        assert "FIBONACCI" in result
        assert "EXAMPLES <NAME>" in result

    def test_examples_load_by_name(self):
        repl, out = make_repl()
        repl.process_line("EXAMPLES HELLO")
        assert 10 in repl.interpreter.lines
        assert "LOADED" in output(out)
        reset_output(out)
        repl.process_line("RUN")
        assert "HELLO" in output(out)

    def test_examples_load_case_insensitive(self):
        repl, out = make_repl()
        repl.process_line("EXAMPLES hello")
        assert 10 in repl.interpreter.lines

    def test_examples_load_with_extension(self):
        repl, out = make_repl()
        repl.process_line("EXAMPLES hello.bas")
        assert 10 in repl.interpreter.lines

    def test_examples_not_found(self):
        repl, out = make_repl()
        repl.process_line("EXAMPLES NONEXISTENT")
        assert "NOT FOUND" in output(out)


# ─── INTEGRATION ─────────────────────────────────────────────────────────


class TestIntegration:
    def test_full_workflow(self):
        """Test a full edit session: enter, find, replace, save, load."""
        repl, out = make_repl()
        repl.process_line('10 PRINT "HELLO WORLD"')
        repl.process_line('20 PRINT "GOODBYE WORLD"')
        repl.process_line("30 END")

        # Find
        reset_output(out)
        repl.process_line('FIND "WORLD"')
        assert "2 LINES FOUND" in output(out)

        # Replace
        reset_output(out)
        repl.process_line('REPLACE "WORLD","EARTH"')
        assert "REPLACED IN 2 LINES" in output(out)

        # Verify
        assert "EARTH" in repl.interpreter.lines[10]
        assert "EARTH" in repl.interpreter.lines[20]

        # Save and reload
        with tempfile.NamedTemporaryFile(suffix=".bas", delete=False) as f:
            fname = f.name
        try:
            repl.process_line(f'SAVE "{fname}"')
            repl.process_line("NEW")
            assert len(repl.interpreter.lines) == 0
            repl.process_line(f'LOAD "{fname}"')
            assert "EARTH" in repl.interpreter.lines[10]
        finally:
            os.unlink(fname)

    def test_edit_delete_workflow(self):
        """EDIT a line, modify, delete old."""
        repl, out = make_repl()
        repl.process_line('10 PRINT "OLD"')
        repl.process_line('20 GOTO 10')

        # EDIT shows the line
        reset_output(out)
        repl.process_line("EDIT 10")
        assert "OLD" in output(out)

        # Replace it
        repl.process_line('10 PRINT "NEW"')
        assert repl.interpreter.lines[10] == 'PRINT "NEW"'

        # Delete line 20
        repl.process_line("DELETE 20")
        assert 20 not in repl.interpreter.lines

    def test_tron_vars_in_loop(self):
        """TRON VARS should show variable changes in FOR loop."""
        out = io.StringIO()
        interp = SafariBasic(out_stream=out)
        interp.add_program_line("10 TRON VARS")
        interp.add_program_line("20 FOR I = 1 TO 3")
        interp.add_program_line("30 NEXT I")
        interp.add_program_line("40 END")
        interp.run_program()
        result = out.getvalue()
        # Should see I changing
        assert "I = 1" in result
