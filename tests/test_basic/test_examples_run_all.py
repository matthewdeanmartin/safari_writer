from __future__ import annotations

import io
from pathlib import Path

import pytest

from safari_basic.interpreter import SafariBasic

EXAMPLES_DIR = Path(__file__).resolve().parents[2] / "safari_basic" / "examples"
EXAMPLE_FILES = sorted(EXAMPLES_DIR.glob("*.bas"), key=lambda path: path.name)

EXPECTED_OUTPUT_SNIPPETS: dict[str, str] = {
    "art.bas": "*   *",
    "fibonacci.bas": "FIBONACCI NUMBERS:",
    "guess.bas": "YOU GOT IT IN 1 GUESSES!",
    "hello.bas": "HELLO, WORLD!",
    "primes.bas": "PRIME NUMBERS UP TO 100:",
}

EXAMPLE_INPUTS: dict[str, str] = {
    "guess.bas": "50\n",
}


def _configure_example_runtime(
    monkeypatch: pytest.MonkeyPatch, example_name: str
) -> str:
    if example_name == "guess.bas":
        monkeypatch.setattr("safari_basic.interpreter.random.random", lambda: 0.49)
    return EXAMPLE_INPUTS.get(example_name, "")


@pytest.mark.parametrize("example_path", EXAMPLE_FILES, ids=lambda path: path.name)
def test_all_basic_examples_run(
    example_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    assert example_path.name in EXPECTED_OUTPUT_SNIPPETS

    output = io.StringIO()
    program_input = io.StringIO(
        _configure_example_runtime(monkeypatch, example_path.name)
    )
    interpreter = SafariBasic(out_stream=output, in_stream=program_input)

    for raw_line in example_path.read_text(encoding="utf-8").splitlines():
        interpreter.add_program_line(raw_line.strip())

    interpreter.run_program()

    rendered = output.getvalue()
    assert rendered
    assert "ERROR:" not in rendered
    assert EXPECTED_OUTPUT_SNIPPETS[example_path.name] in rendered
