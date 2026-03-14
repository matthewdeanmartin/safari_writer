"""Tests for Safari ASM."""

from __future__ import annotations

import io
import math
from pathlib import Path

import pytest
import safari_asm
from safari_asm import SafariAsmInterpreter, parse_args
from safari_asm.parser import parse_source
from safari_asm.main import main as safari_asm_main

EXAMPLE_DIR = Path(__file__).resolve().parents[2] / "safari_asm" / "example"


def run_program(
    source: str,
    *,
    argv: list[str] | None = None,
    stdin_text: str = "",
) -> tuple[SafariAsmInterpreter, str, str]:
    stdout = io.StringIO()
    stderr = io.StringIO()
    interpreter = SafariAsmInterpreter(
        argv=argv,
        stdin=io.StringIO(stdin_text),
        stdout=stdout,
        stderr=stderr,
    )
    interpreter.run_source(source)
    return interpreter, stdout.getvalue(), stderr.getvalue()


def run_example(
    filename: str,
    *,
    argv: list[str] | None = None,
    stdin_text: str = "",
) -> tuple[SafariAsmInterpreter, str, str]:
    source = (EXAMPLE_DIR / filename).read_text(encoding="utf-8")
    return run_program(source, argv=argv, stdin_text=stdin_text)


def assert_example_runs(
    filename: str,
    *,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    argv: list[str] | None = None
    stdin_text = ""
    dst: Path | None = None

    if filename == "01_prompt_name.asm":
        stdin_text = "  Matt  \n"
    elif filename in {"02_echo_stdin.asm", "03_count_stdin_lines.asm"}:
        stdin_text = "ALPHA\nBETA\n"
    elif filename == "07_csv_split.asm":
        stdin_text = "LEFT,RIGHT\n"
    elif filename == "10_cli_args.asm":
        argv = ["LEFT", "RIGHT"]
    elif filename == "11_env_lookup.asm":
        monkeypatch.setenv("SAFARI_ASM_DEMO", "retro")
    elif filename == "12_file_copy.asm":
        src = tmp_path / "source.txt"
        dst = tmp_path / "dest.txt"
        src.write_text("ALPHA\nBETA\n", encoding="utf-8")
        argv = [str(src), str(dst)]
    elif filename == "15_friendly_style.asm":
        stdin_text = "  Ada  \n"
    elif filename == "16_text_pipeline.asm":
        stdin_text = "  cat nap  \n"

    _, stdout, stderr = run_example(filename, argv=argv, stdin_text=stdin_text)

    match filename:
        case "00_hello_world.asm":
            assert stdout == "HELLO FROM SAFARI ASM\n"
            assert stderr == ""
        case "01_prompt_name.asm":
            assert stdout == "ENTER YOUR NAME: HELLO, Matt!\n"
            assert stderr == ""
        case "02_echo_stdin.asm":
            assert stdout == "ALPHA\nBETA\n"
            assert stderr == ""
        case "03_count_stdin_lines.asm":
            assert stdout == "LINES=2\n"
            assert stderr == ""
        case "04_numeric_loop.asm":
            assert stdout.splitlines() == ["1", "2", "3", "4", "5"]
            assert stderr == ""
        case "05_subroutine_greeting.asm":
            assert stdout == "HELLO, MATT!\n"
            assert stderr == ""
        case "06_stack_roundtrip.asm":
            assert stdout.splitlines() == ["SECOND", "FIRST"]
            assert stderr == ""
        case "07_csv_split.asm":
            assert stdout == "LEFT=LEFT RIGHT=RIGHT\n"
            assert stderr == ""
        case "08_collections.asm":
            assert stdout == "RED|GREEN|BLUE MODE=FAST DEBUG=TRUE\n"
            assert stderr == ""
        case "09_indexed_access.asm":
            assert stdout.splitlines() == ["BETA", "CENTER"]
            assert stderr == ""
        case "10_cli_args.asm":
            assert stdout == "LEFT=LEFT RIGHT=RIGHT\n"
            assert stderr == ""
        case "11_env_lookup.asm":
            assert stdout == "ENV=retro\n"
            assert stderr == ""
        case "12_file_copy.asm":
            assert stdout == ""
            assert stderr == ""
            assert dst is not None
            assert dst.read_text(encoding="utf-8") == "ALPHA\nBETA\n"
        case "13_python_bridge.asm":
            assert stdout == "apple,banana,pear LEN=4\n"
            assert stderr == ""
        case "14_error_branch.asm":
            assert stdout == ""
            assert "missing-file.txt" in stderr
        case "15_friendly_style.asm":
            assert stdout == "WHAT IS YOUR NAME? HELLO, Ada!\n"
            assert stderr == ""
        case "16_text_pipeline.asm":
            assert stdout == "DOG NAP LEN=7\n"
            assert stderr == ""
        case _:
            raise AssertionError(f"Unhandled ASM example: {filename}")


def test_public_exports_are_explicit():
    expected = {
        "ConditionState",
        "Directive",
        "Instruction",
        "Operand",
        "Program",
        "SafariAsmInterpreter",
        "SafariAsmParseError",
        "SafariAsmRuntimeError",
        "SymbolDeclaration",
        "build_parser",
        "main",
        "parse_args",
        "parse_source",
        "run_source",
    }

    assert expected.issubset(set(safari_asm.__all__))


def test_parse_args_supports_file_and_program_args():
    args = parse_args(["demo.asm", "--", "left", "right"])

    assert args.file == "demo.asm"
    assert args.program_args == ["left", "right"]


def test_example_folder_contains_copious_scripts():
    example_files = sorted(EXAMPLE_DIR.glob("*.asm"))

    assert len(example_files) >= 12


def test_all_example_scripts_parse():
    for path in sorted(EXAMPLE_DIR.glob("*.asm")):
        program = parse_source(path.read_text(encoding="utf-8"), source_name=str(path))
        assert program.instructions, (
            f"{path.name} should contain executable instructions"
        )


@pytest.mark.parametrize(
    "example_path",
    sorted(EXAMPLE_DIR.glob("*.asm")),
    ids=lambda path: path.name,
)
def test_all_example_scripts_run(
    example_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
):
    assert_example_runs(example_path.name, monkeypatch=monkeypatch, tmp_path=tmp_path)


def test_hello_world_program():
    _, stdout, stderr = run_program(
        """
        .TEXT
        MAIN:
            LDA #"HELLO, WORLD!"
            OUTLN A
            HALT
        """
    )

    assert stdout == "HELLO, WORLD!\n"
    assert stderr == ""


def test_example_hello_world_runs():
    _, stdout, stderr = run_example("00_hello_world.asm")

    assert stdout == "HELLO FROM SAFARI ASM\n"
    assert stderr == ""


def test_prompt_and_concat_program():
    _, stdout, _ = run_program(
        """
        .DATA
        NAME:   .VAR
        PROMPT: .CONST "ENTER YOUR NAME: "

        .TEXT
        MAIN:
            LDA PROMPT
            OUT A
            INP A
            TRIM A
            STA NAME
            LDA #"HELLO, "
            CAT A, NAME
            CAT A, #"!"
            OUTLN A
            HALT
        """,
        stdin_text="  Matt  \n",
    )

    assert stdout == "ENTER YOUR NAME: HELLO, Matt!\n"


def test_example_prompt_name_runs():
    _, stdout, stderr = run_example("01_prompt_name.asm", stdin_text="  Matt  \n")

    assert stdout == "ENTER YOUR NAME: HELLO, Matt!\n"
    assert stderr == ""


def test_example_echo_and_count_stdin_runs():
    _, echo_stdout, _ = run_example("02_echo_stdin.asm", stdin_text="ALPHA\nBETA\n")
    _, count_stdout, _ = run_example(
        "03_count_stdin_lines.asm", stdin_text="ALPHA\nBETA\n"
    )

    assert echo_stdout == "ALPHA\nBETA\n"
    assert count_stdout == "LINES=2\n"


def test_numeric_loop_and_case_insensitive_aliases():
    _, stdout, _ = run_program(
        """
        .data
        i: .var

        .text
        main:
            loada #1
            storea i
        loop:
            lda i
            compare a, #3
            bgt done
            println a
            increment i
            branch loop
        done:
            stop
        """
    )

    assert stdout.splitlines() == ["1", "2", "3"]


def test_example_loop_stack_and_subroutine_run():
    _, loop_stdout, _ = run_example("04_numeric_loop.asm")
    _, greeting_stdout, _ = run_example("05_subroutine_greeting.asm")
    _, stack_stdout, _ = run_example("06_stack_roundtrip.asm")

    assert loop_stdout.splitlines() == ["1", "2", "3", "4", "5"]
    assert greeting_stdout == "HELLO, MATT!\n"
    assert stack_stdout.splitlines() == ["SECOND", "FIRST"]


def test_subroutine_stack_and_return_value():
    _, stdout, _ = run_program(
        """
        .DATA
        NAME: .VAR

        .TEXT
        .ENTRY MAIN
        MAIN:
            LDA #"MATT"
            JSR GREET
            OUTLN A
            HALT

        GREET:
            PHA
            STA NAME
            LDA #"HELLO, "
            CAT A, NAME
            PLA
            RTS
        """
    )

    assert stdout == "MATT\n"


def test_example_collections_and_csv_examples_run():
    _, csv_stdout, _ = run_example("07_csv_split.asm", stdin_text="LEFT,RIGHT\n")
    _, collections_stdout, _ = run_example("08_collections.asm")
    _, indexed_stdout, _ = run_example("09_indexed_access.asm")

    assert csv_stdout == "LEFT=LEFT RIGHT=RIGHT\n"
    assert collections_stdout == "RED|GREEN|BLUE MODE=FAST DEBUG=TRUE\n"
    assert indexed_stdout.splitlines() == ["BETA", "CENTER"]


def test_split_get_put_join_and_replace():
    interpreter, stdout, _ = run_program(
        """
        .DATA
        ITEMS: .LIST "RED", "GREEN"
        SETTINGS: .MAP "MODE", "FAST"

        .TEXT
        MAIN:
            LDA #"LEFT,RIGHT"
            SPLIT X, A, #","
            GET Y, X, #0
            GET A, X, #1
            PUT SETTINGS, #"DEBUG", TRUE
            REPL A, A, #"RIGHT", #"DONE"
            JOIN A, ITEMS, #"|"
            OUTLN A
            HALT
        """
    )

    assert stdout == "RED|GREEN\n"
    assert interpreter.variables["SETTINGS"]["DEBUG"] is True


def test_example_cli_args_and_env_examples_run(monkeypatch):
    monkeypatch.setenv("SAFARI_ASM_DEMO", "retro")

    _, cli_stdout, cli_stderr = run_example(
        "10_cli_args.asm",
        argv=["LEFT", "RIGHT"],
    )
    _, env_stdout, env_stderr = run_example("11_env_lookup.asm")

    assert cli_stdout == "LEFT=LEFT RIGHT=RIGHT\n"
    assert cli_stderr == ""
    assert env_stdout == "ENV=retro\n"
    assert env_stderr == ""


def test_file_copy_program(tmp_path):
    src = tmp_path / "source.txt"
    dst = tmp_path / "dest.txt"
    src.write_text("ALPHA\nBETA\n", encoding="utf-8")

    _, stdout, stderr = run_program(
        """
        .DATA
        SRC: .VAR
        DST: .VAR

        .TEXT
        MAIN:
            ARG A, #0
            BEQ USAGE
            STA SRC
            ARG A, #1
            BEQ USAGE
            STA DST
            OPEN IN, SRC, #"r"
            BERR FAILSRC
            OPEN OUT, DST, #"w"
            BERR FAILDST
        COPYLOOP:
            READLN A, IN
            BEQ DONE
            WRITELN OUT, A
            JMP COPYLOOP
        DONE:
            CLOSE IN
            CLOSE OUT
            HALT
        FAILSRC:
            ERRLN #"CANNOT OPEN SOURCE FILE"
            HALT
        FAILDST:
            ERRLN #"CANNOT OPEN DESTINATION FILE"
            CLOSE IN
            HALT
        USAGE:
            ERRLN #"USAGE"
            HALT
        """,
        argv=[str(src), str(dst)],
    )

    assert stdout == ""
    assert stderr == ""
    assert dst.read_text(encoding="utf-8") == src.read_text(encoding="utf-8")


def test_example_file_copy_runs(tmp_path):
    src = tmp_path / "source.txt"
    dst = tmp_path / "dest.txt"
    src.write_text("ALPHA\nBETA\n", encoding="utf-8")

    _, stdout, stderr = run_example(
        "12_file_copy.asm",
        argv=[str(src), str(dst)],
    )

    assert stdout == ""
    assert stderr == ""
    assert dst.read_text(encoding="utf-8") == "ALPHA\nBETA\n"


def test_pycall_supports_builtins_and_modules():
    interpreter, stdout, _ = run_program(
        """
        .DATA
        NAME: .VAR "MATT"

        .TEXT
        MAIN:
            PYCALL X, #"len", NAME
            PYCALL A, #"math:sqrt", #144
            OUTLN A
            HALT
        """,
    )

    assert math.isclose(float(stdout.strip()), 12.0)
    assert interpreter.registers["X"] == 4


def test_example_python_bridge_error_and_text_pipeline_run():
    _, bridge_stdout, bridge_stderr = run_example("13_python_bridge.asm")
    _, error_stdout, error_stderr = run_example("14_error_branch.asm")
    _, friendly_stdout, friendly_stderr = run_example(
        "15_friendly_style.asm",
        stdin_text="  Ada  \n",
    )
    _, pipeline_stdout, pipeline_stderr = run_example(
        "16_text_pipeline.asm",
        stdin_text="  cat nap  \n",
    )

    assert bridge_stdout == "apple,banana,pear LEN=4\n"
    assert bridge_stderr == ""
    assert error_stdout == ""
    assert "missing-file.txt" in error_stderr
    assert friendly_stdout == "WHAT IS YOUR NAME? HELLO, Ada!\n"
    assert friendly_stderr == ""
    assert pipeline_stdout == "DOG NAP LEN=7\n"
    assert pipeline_stderr == ""


def test_pycall_failure_sets_error_for_berr():
    interpreter, stdout, stderr = run_program(
        """
        .TEXT
        MAIN:
            PYCALL A, #"missing:thing"
            BERR FAIL
            OUTLN #"OK"
            HALT
        FAIL:
            ERRMSG X
            ERRLN X
            HALT
        """
    )

    assert stdout == ""
    assert "No module named" in stderr
    assert interpreter.flags.error_message is None


def test_cli_runs_file_and_returns_zero(tmp_path, monkeypatch):
    program = tmp_path / "hello.asm"
    program.write_text(
        """
        .TEXT
        MAIN:
            OUTLN #"HI"
            HALT
        """,
        encoding="utf-8",
    )
    stdout = io.StringIO()
    stderr = io.StringIO()
    monkeypatch.setattr("sys.stdout", stdout)
    monkeypatch.setattr("sys.stderr", stderr)

    exit_code = safari_asm_main([str(program)])

    assert exit_code == 0
    assert stdout.getvalue() == "HI\n"
    assert stderr.getvalue() == ""


def test_cli_rejects_missing_file(tmp_path, monkeypatch):
    missing = tmp_path / "missing.asm"
    stderr = io.StringIO()
    monkeypatch.setattr("sys.stderr", stderr)

    exit_code = safari_asm_main([str(missing)])

    assert exit_code == 2
    assert f"File not found: {missing.resolve()}" in stderr.getvalue()
