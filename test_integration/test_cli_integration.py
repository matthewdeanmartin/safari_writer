import os
import subprocess
from pathlib import Path

import pytest

# Script names defined in pyproject.toml
SCRIPTS = [
    "safari-writer",
    "safari-dos",
    "safari-chat",
    "safari-base",
    "safari-fed",
    "safari-asm",
    "safari-repl",
    "safari-reader",
    "safari-slides",
    "safari-view",
]


@pytest.mark.parametrize("script", SCRIPTS)
def test_cli_help(script):
    """Test that --help works for each CLI script."""
    try:
        result = subprocess.run(
            ["uv", "run", script, "--help"],
            capture_output=True,
            text=True,
            timeout=10.0,
        )
        output = result.stdout.lower() + result.stderr.lower()
        # Some might exit with 0, others with 1 or 2 on help, but should print usage
        assert "usage:" in output or "help" in output
    except subprocess.TimeoutExpired:
        pytest.fail(f"{script} --help timed out")


@pytest.mark.parametrize("script", SCRIPTS)
def test_cli_tui_startup_headless(script):
    """Test that the TUI starts up and exits cleanly in headless mode."""
    # We use the SAFARI_HEADLESS environment variable we just added
    env = os.environ.copy()
    env["SAFARI_HEADLESS"] = "1"

    try:
        result = subprocess.run(
            ["uv", "run", script], env=env, timeout=15.0, capture_output=True, text=True
        )
        # In headless mode, it should exit with 0 after mounting
        assert result.returncode == 0
    except subprocess.TimeoutExpired:
        pytest.fail(f"{script} hang even in SAFARI_HEADLESS mode")
    except subprocess.CalledProcessError as e:
        pytest.fail(f"{script} crashed on startup: {e.stderr}")


def test_safari_writer_export_ansi(tmp_path):
    """Test a headless command for safari-writer."""
    doc = tmp_path / "test.sfw"
    doc.write_text("Hello World", encoding="utf-8")

    result = subprocess.run(
        ["uv", "run", "safari-writer", "export", "ansi", str(doc), "--stdout"],
        capture_output=True,
        text=True,
        timeout=10.0,
    )
    assert result.returncode == 0
    assert "Hello World" in result.stdout


def test_safari_asm_run(tmp_path):
    """Test safari-asm with a simple program."""
    asm_file = tmp_path / "test.asm"
    asm_file.write_text('PRINT "HELLO"\n', encoding="utf-8")

    result = subprocess.run(
        ["uv", "run", "safari-asm", str(asm_file)],
        capture_output=True,
        text=True,
        timeout=10.0,
    )
    assert result.returncode == 0
    assert "HELLO" in result.stdout.strip()
