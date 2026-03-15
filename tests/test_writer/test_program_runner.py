from pathlib import Path

from safari_writer.file_types import resolve_file_profile
from safari_writer.program_runner import (
    is_runnable_path,
    run_program_file,
    run_program_source,
)


def test_is_runnable_path_recognizes_supported_extensions(tmp_path):
    assert is_runnable_path(tmp_path / "demo.bas") is True
    assert is_runnable_path(tmp_path / "demo.asm") is True
    assert is_runnable_path(tmp_path / "demo.prg") is True
    assert is_runnable_path(tmp_path / "demo.py") is True
    assert is_runnable_path(tmp_path / "demo.txt") is False


def test_run_program_file_executes_basic_source(tmp_path):
    program = tmp_path / "hello.bas"
    program.write_text('10 PRINT "HI"', encoding="utf-8")

    result = run_program_file(program)

    assert result.success is True
    assert result.title == "SAFARI BASIC OUTPUT"
    assert result.output == "HI"


def test_run_program_source_honors_prg_workdir_directive(tmp_path):
    script_dir = tmp_path / "scripts"
    data_dir = script_dir / "data"
    script_dir.mkdir()
    data_dir.mkdir()

    result = run_program_source(
        "\n".join(
            [
                "* SAFARI_WORKDIR: data",
                "CREATE TABLE mytest (name C 10)",
                "APPEND BLANK",
                'REPLACE name WITH "Alice"',
                "LIST ALL",
            ]
        ),
        profile=resolve_file_profile("report.prg"),
        filename="report.prg",
        working_path=script_dir / "report.prg",
    )

    assert result.success is True
    assert "Alice" in result.output
    assert (data_dir / "mytest.dbf").exists()


def test_run_program_file_executes_asm_with_prompt_input(tmp_path):
    program = tmp_path / "hello.asm"
    program.write_text(
        "\n".join(
            [
                ".TEXT",
                "MAIN:",
                '    OUT #"NAME: "',
                "    INP A",
                '    CAT A, #"!"',
                "    OUTLN A",
                "    HALT",
            ]
        ),
        encoding="utf-8",
    )

    result = run_program_file(program, stdin_text="Ada\n")

    assert result.success is True
    assert result.title == "SAFARI ASM OUTPUT"
    assert result.output == "NAME: Ada!"
