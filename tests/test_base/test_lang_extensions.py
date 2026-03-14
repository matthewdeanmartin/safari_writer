import pytest
from pathlib import Path
from safari_base.lang.interpreter import Interpreter


def test_append_blank_and_replace(tmp_path):
    # Set work_dir to tmp_path to handle temporary files safely
    from safari_base.lang.environment import Environment

    env = Environment(work_dir=tmp_path)
    interpreter = Interpreter(env=env)

    source = """
CREATE TABLE mytest (name C 10, val N 5)
APPEND BLANK
REPLACE name WITH "Alice", val WITH 42
APPEND BLANK
REPLACE name WITH "Bob", val WITH 123
LIST ALL
"""
    result = interpreter.run_source(source)

    assert result.success is True
    assert "Alice" in result.data
    assert "Bob" in result.data
    assert "42" in result.data
    assert "123" in result.data

    # Verify file existence in tmp_path
    assert (tmp_path / "mytest.dbf").exists()


def test_do_command(tmp_path):
    # Test executing a .prg file
    from safari_base.lang.environment import Environment

    env = Environment(work_dir=tmp_path)
    interpreter = Interpreter(env=env)

    prg_content = """
? "Hello from PRG"
x = 10 * 10
? "Result: " + STR(x)
"""
    prg_file = tmp_path / "test.prg"
    prg_file.write_text(prg_content)

    result = interpreter.run_program(prg_file)
    assert result.success is True
    assert "Hello from PRG" in result.data
    assert "Result: 100" in result.data
