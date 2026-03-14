import io
import pytest
from safari_basic.interpreter import SafariBasic, BasicError

def run_expr(expr: str) -> str:
    out = io.StringIO()
    interp = SafariBasic(out_stream=out)
    # Inject some variables for testing
    interp.vars["A"] = 10.0
    interp.vars["B"] = 20.0
    interp.string_caps["S$"] = 100
    interp.vars["S$"] = "HELLO"
    interp.string_caps["T$"] = 100
    interp.vars["T$"] = "WORLD"
    
    interp.execute_immediate(f"PRINT {expr}")
    return out.getvalue().strip()

def test_precedence_arithmetic():
    # Standard PEMDAS/BODMAS
    assert run_expr("2 + 3 * 4") == "14"
    assert run_expr("(2 + 3) * 4") == "20"
    assert run_expr("2 * 3 ^ 2") == "18"
    assert run_expr("(2 * 3) ^ 2") == "36"
    assert run_expr("10 - 5 - 2") == "3"  # Left associative
    assert run_expr("12 / 4 / 3") == "1"   # Left associative

def test_precedence_comparison():
    # Comparison should have lower precedence than arithmetic
    # 1 + 2 < 3 + 4  =>  3 < 7  => 1.0
    assert run_expr("1 + 2 < 3 + 4") == "1"
    # 10 > 5 + 2    =>  10 > 7  => 1.0
    assert run_expr("10 > 5 + 2") == "1"
    # 2 + 3 = 5     =>  5 = 5   => 1.0
    assert run_expr("2 + 3 = 5") == "1"
    # 2 + 3 <> 6    =>  5 <> 6  => 1.0
    assert run_expr("2 + 3 <> 6") == "1"

def test_complex_precedence():
    # Mixed arithmetic and comparison
    # (2 + 3 * 4 > 10) => (2 + 12 > 10) => (14 > 10) => 1.0
    assert run_expr("2 + 3 * 4 > 10") == "1"
    # (2 + 3 * 4 < 10) => (14 < 10) => 0.0
    assert run_expr("2 + 3 * 4 < 10") == "0"

def test_string_expressions():
    assert run_expr('S$ + " " + T$') == "HELLO WORLD"
    assert run_expr('S$ = "HELLO"') == "1"
    assert run_expr('S$ <> "WORLD"') == "1"
    assert run_expr('S$ < T$') == "1" # "HELLO" < "WORLD"
    assert run_expr('S$ > T$') == "0"

def test_functions():
    assert run_expr("ABS(-10)") == "10"
    assert run_expr("INT(3.7)") == "3"
    assert run_expr("SQR(16)") == "4"
    assert run_expr('LEN(S$)') == "5"
    assert run_expr('VAL("123.45")') == "123.45"
    assert run_expr('STR$(123)') == "123"
    assert run_expr('ASC("ABC")') == "65"
    assert run_expr('CHR$(65)') == "A"

def test_type_errors():
    with pytest.raises(BasicError, match="Type mismatch"):
        run_expr('A + S$')
    with pytest.raises(BasicError, match="Type mismatch"):
        run_expr('S$ - T$')
    with pytest.raises(BasicError, match="Type mismatch in comparison"):
        run_expr('A = S$')

def test_unuary_operators():
    assert run_expr("-5 + 10") == "5"
    assert run_expr("10 + -5") == "5"
    assert run_expr("--5") == "5"
    assert run_expr("---5") == "-5"
    assert run_expr("+5") == "5"

def test_division_by_zero():
    with pytest.raises(BasicError, match="Division by zero"):
        run_expr("10 / 0")

def test_nested_parentheses():
    assert run_expr("((2 + 3) * (4 + 5))") == "45"
    assert run_expr("1 + (2 * (3 + 4))") == "15"
