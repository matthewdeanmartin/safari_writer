import io
import pytest
from safari_basic.interpreter import SafariBasic, BasicError
from safari_basic.repl import SafariREPL


def test_basic_print():
    out = io.StringIO()
    interp = SafariBasic(out_stream=out)
    interp.execute_immediate('PRINT "HELLO WORLD"')
    assert out.getvalue().strip() == "HELLO WORLD"


def test_arithmetic():
    out = io.StringIO()
    interp = SafariBasic(out_stream=out)
    interp.execute_immediate("PRINT 2 + 3 * 4")
    assert out.getvalue().strip() == "14"


def test_variables():
    out = io.StringIO()
    interp = SafariBasic(out_stream=out)
    interp.execute_immediate("A = 10")
    interp.execute_immediate("PRINT A * 2")
    assert out.getvalue().strip() == "20"


def test_program_loop():
    out = io.StringIO()
    interp = SafariBasic(out_stream=out)
    interp.add_program_line("10 FOR I = 1 TO 3")
    interp.add_program_line("20 PRINT I")
    interp.add_program_line("30 NEXT I")
    interp.run_program()
    assert out.getvalue().splitlines() == ["1", "2", "3"]


def test_renumber():
    interp = SafariBasic()
    interp.add_program_line('10 PRINT "HI"')
    interp.add_program_line("20 GOTO 10")
    interp.renumber(start=100, step=10)
    assert 100 in interp.lines
    assert 110 in interp.lines
    assert "GOTO 100" in interp.lines[110]


def test_tron_troff():
    out = io.StringIO()
    interp = SafariBasic(out_stream=out)
    interp.add_program_line("10 TRON")
    interp.add_program_line('20 PRINT "HI"')
    interp.add_program_line("30 TROFF")
    interp.add_program_line('40 PRINT "BYE"')
    interp.run_program()
    output = out.getvalue()
    assert "[20]" in output
    assert "HI" in output
    assert "[30]" in output
    assert "[40]" not in output
    assert "BYE" in output


def test_repl_undo_redo():
    repl = SafariREPL(out_stream=io.StringIO())
    repl.process_line('10 PRINT "A"')
    assert 10 in repl.interpreter.lines
    repl.process_line("UNDO")
    assert 10 not in repl.interpreter.lines
    repl.process_line("REDO")
    assert 10 in repl.interpreter.lines


def test_string_concatenation():
    out = io.StringIO()
    interp = SafariBasic(out_stream=out)
    interp.execute_immediate("DIM A$(10), B$(10)")
    interp.execute_immediate('A$ = "HELLO"')
    interp.execute_immediate('B$ = " WORLD"')
    interp.execute_immediate("PRINT A$ + B$")
    assert out.getvalue().strip() == "HELLO WORLD"


def test_if_then_line():
    out = io.StringIO()
    interp = SafariBasic(out_stream=out)
    interp.add_program_line("10 IF 1 THEN 30")
    interp.add_program_line('20 PRINT "NO"')
    interp.add_program_line('30 PRINT "YES"')
    interp.run_program()
    assert "YES" in out.getvalue()
    assert "NO" not in out.getvalue()
