from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from safari_base.lang.environment import Environment
from safari_base.lang.interpreter import Interpreter

EXAMPLES_DIR = Path(__file__).resolve().parents[2] / "safari_base" / "examples"
EXAMPLE_PROGRAMS = sorted(EXAMPLES_DIR.glob("*.prg"), key=lambda path: path.name)

EXPECTED_OUTPUT_SNIPPETS: dict[str, tuple[str, ...]] = {
    "demo_calc.prg": ("Final sum: 55", "Value is medium: 42", "Demo completed."),
    "demo_create.prg": (
        "Creating customers table...",
        "Found: Charlie Brown",
        "with balance 2100.75",
        "Records > 1000: 2",
        "Demo completed.",
    ),
    "demo_func.prg": (
        "Square of 5 is: 25",
        "Hello, User!",
        "Welcome to Safari Base.",
        "Cube of 3 is: 27",
        "Demo completed.",
    ),
    "demo_hash.prg": (
        "User: matt",
        "Key: port = 8080",
        "Demo completed.",
    ),
}


@pytest.mark.parametrize("example_path", EXAMPLE_PROGRAMS, ids=lambda path: path.name)
def test_all_base_examples_run(example_path: Path, tmp_path: Path) -> None:
    assert example_path.name in EXPECTED_OUTPUT_SNIPPETS

    staged_program = tmp_path / example_path.name
    shutil.copy2(example_path, staged_program)

    env = Environment(work_dir=tmp_path)
    interpreter = Interpreter(env=env)
    result = interpreter.run_program(staged_program)

    assert result.success is True
    rendered = result.data or result.message
    assert rendered

    for snippet in EXPECTED_OUTPUT_SNIPPETS[example_path.name]:
        assert snippet in rendered
