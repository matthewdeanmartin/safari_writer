"""Shared execution helpers for runnable Safari source files."""

from __future__ import annotations

import io
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

from safari_writer.file_types import FileProfile, HighlightProfile, resolve_file_profile

__all__ = [
    "decode_stdin_text",
    "ProgramExecutionResult",
    "is_runnable_path",
    "is_runnable_profile",
    "path_may_need_stdin",
    "program_may_need_stdin",
    "run_program_file",
    "run_program_source",
]

_RUNNABLE_PROFILES = frozenset(
    {
        HighlightProfile.SAFARI_BASIC,
        HighlightProfile.SAFARI_ASM,
        HighlightProfile.SAFARI_BASE,
        HighlightProfile.PYTHON,
    }
)

_BASE_DIRECTIVE_RE = re.compile(
    r"^\s*\*\s*SAFARI_(WORKDIR|DB|DATABASE)\s*:\s*(?P<value>.+?)\s*$",
    re.IGNORECASE,
)
_BASIC_INPUT_RE = re.compile(r"\bINPUT\b", re.IGNORECASE)
_ASM_INPUT_RE = re.compile(r"\b(INP|READLN)\b", re.IGNORECASE)
_PYTHON_INPUT_RE = re.compile(r"\binput\s*\(", re.IGNORECASE)


@dataclass(frozen=True)
class ProgramExecutionResult:
    """Captured program output ready for display in the UI or CLI."""

    title: str
    output: str
    success: bool


def is_runnable_profile(profile: FileProfile) -> bool:
    """Return True when a file profile can be executed directly."""

    return profile.highlight_profile in _RUNNABLE_PROFILES


def is_runnable_path(path: Path) -> bool:
    """Return True when a path resolves to an executable source profile."""

    return is_runnable_profile(resolve_file_profile(path.name))


def program_may_need_stdin(source: str, profile: FileProfile) -> bool:
    """Best-effort check for programs that appear to read stdin."""

    if profile.highlight_profile == HighlightProfile.SAFARI_BASIC:
        return _BASIC_INPUT_RE.search(source) is not None
    if profile.highlight_profile == HighlightProfile.SAFARI_ASM:
        return _ASM_INPUT_RE.search(source) is not None
    if profile.highlight_profile == HighlightProfile.PYTHON:
        return _PYTHON_INPUT_RE.search(source) is not None
    return False


def path_may_need_stdin(path: Path) -> bool:
    """Best-effort input detection for a runnable file on disk."""

    resolved = path.resolve()
    profile = resolve_file_profile(resolved.name)
    if not is_runnable_profile(profile):
        return False
    try:
        source = resolved.read_text(encoding="utf-8")
    except OSError:
        return False
    return program_may_need_stdin(source, profile)


def decode_stdin_text(value: str | None) -> str:
    """Decode lightweight escaped input entered into a single-line prompt."""

    if not value:
        return ""
    text = value
    for raw, decoded in (
        ("\\r\\n", "\r\n"),
        ("\\n", "\n"),
        ("\\r", "\r"),
        ("\\t", "\t"),
    ):
        text = text.replace(raw, decoded)
    return text


def run_program_file(
    path: Path,
    *,
    database_path: Path | None = None,
    stdin_text: str | None = None,
) -> ProgramExecutionResult:
    """Execute a supported source file from disk and capture its output."""

    resolved = path.resolve()
    profile = resolve_file_profile(resolved.name)
    if not is_runnable_profile(profile):
        return ProgramExecutionResult(
            title="EXECUTION OUTPUT",
            output="No runner available for this file type",
            success=False,
        )
    try:
        source = resolved.read_text(encoding="utf-8")
    except OSError as exc:
        return ProgramExecutionResult(
            title="EXECUTION OUTPUT",
            output=f"RUN ERROR: {exc}",
            success=False,
        )
    return run_program_source(
        source,
        profile=profile,
        filename=resolved.name,
        working_path=resolved,
        database_path=database_path,
        stdin_text=stdin_text,
    )


def run_program_source(
    source: str,
    *,
    profile: FileProfile,
    filename: str | None = None,
    working_path: Path | None = None,
    database_path: Path | None = None,
    stdin_text: str | None = None,
) -> ProgramExecutionResult:
    """Execute source text using the runtime matching its file profile."""

    if not is_runnable_profile(profile):
        return ProgramExecutionResult(
            title="EXECUTION OUTPUT",
            output="No runner available for this file type",
            success=False,
        )

    if profile.highlight_profile == HighlightProfile.SAFARI_BASIC:
        return _run_basic(source, stdin_text=stdin_text)
    if profile.highlight_profile == HighlightProfile.SAFARI_ASM:
        return _run_asm(source, stdin_text=stdin_text)
    if profile.highlight_profile == HighlightProfile.SAFARI_BASE:
        return _run_base(
            source,
            filename=filename,
            working_path=working_path,
            database_path=database_path,
        )
    if profile.highlight_profile == HighlightProfile.PYTHON:
        return _run_python(
            source,
            working_path=working_path,
            stdin_text=stdin_text,
        )

    return ProgramExecutionResult(
        title="EXECUTION OUTPUT",
        output="No runner available for this file type",
        success=False,
    )


def _run_basic(source: str, *, stdin_text: str | None) -> ProgramExecutionResult:
    from safari_basic.interpreter import BasicError, SafariBasic

    buf = io.StringIO()
    basic_interp = SafariBasic(
        out_stream=buf,
        in_stream=io.StringIO(stdin_text or ""),
    )
    try:
        basic_interp.reset()
        for line in source.splitlines():
            basic_interp.add_program_line(line.strip())
        basic_interp.run_program()
        return ProgramExecutionResult(
            title="SAFARI BASIC OUTPUT",
            output=_normalize_output(buf.getvalue()),
            success=True,
        )
    except BasicError as exc:
        return ProgramExecutionResult(
            title="SAFARI BASIC OUTPUT",
            output=f"BASIC ERROR: {exc}",
            success=False,
        )
    except Exception as exc:
        return ProgramExecutionResult(
            title="SAFARI BASIC OUTPUT",
            output=f"SYSTEM ERROR: {exc}",
            success=False,
        )


def _run_asm(source: str, *, stdin_text: str | None) -> ProgramExecutionResult:
    from safari_asm.interpreter import run_source as run_asm

    buf = io.StringIO()
    try:
        run_asm(
            source,
            stdin=io.StringIO(stdin_text or ""),
            stdout=buf,
            stderr=buf,
        )
        return ProgramExecutionResult(
            title="SAFARI ASM OUTPUT",
            output=_normalize_output(buf.getvalue()),
            success=True,
        )
    except Exception as exc:
        return ProgramExecutionResult(
            title="SAFARI ASM OUTPUT",
            output=f"ASM ERROR: {exc}",
            success=False,
        )


def _run_base(
    source: str,
    *,
    filename: str | None,
    working_path: Path | None,
    database_path: Path | None,
) -> ProgramExecutionResult:
    from safari_base.lang.environment import Environment as BaseEnvironment
    from safari_base.lang.interpreter import Interpreter as BaseInterpreter

    work_dir = _resolve_base_work_dir(
        source, working_path=working_path, database_path=database_path
    )
    program_name = Path(filename).stem if filename else "<input>"
    try:
        env = BaseEnvironment(work_dir=work_dir, default_dir=work_dir)
        base_interp = BaseInterpreter(env)
        base_result = base_interp.run_source(source, program_name=program_name)
        output = base_result.data or base_result.message or ""
        if (
            base_result.message
            and base_result.data
            and base_result.message != base_result.data
        ):
            output = f"{base_result.message}\n\n{base_result.data}"
        return ProgramExecutionResult(
            title="SAFARI BASE OUTPUT",
            output=_normalize_output(output),
            success=base_result.success,
        )
    except Exception as exc:
        return ProgramExecutionResult(
            title="SAFARI BASE OUTPUT",
            output=f"BASE ERROR: {exc}",
            success=False,
        )


def _run_python(
    source: str,
    *,
    working_path: Path | None,
    stdin_text: str | None,
) -> ProgramExecutionResult:
    temp_name: str | None = None
    cwd = working_path.parent if working_path is not None else None
    temp_dir = cwd if cwd is not None and cwd.exists() else None
    try:
        with tempfile.NamedTemporaryFile(
            suffix=".py",
            delete=False,
            dir=temp_dir,
            mode="w",
            encoding="utf-8",
        ) as handle:
            handle.write(source)
            temp_name = handle.name

        python_result = subprocess.run(
            [sys.executable, temp_name],
            input=stdin_text or "",
            capture_output=True,
            text=True,
            timeout=10,
            cwd=cwd,
        )
        return ProgramExecutionResult(
            title="PYTHON OUTPUT",
            output=_normalize_output(python_result.stdout + python_result.stderr),
            success=python_result.returncode == 0,
        )
    except Exception as exc:
        return ProgramExecutionResult(
            title="PYTHON OUTPUT",
            output=f"PYTHON ERROR: {exc}",
            success=False,
        )
    finally:
        if temp_name is not None:
            try:
                Path(temp_name).unlink()
            except OSError:
                pass


def _resolve_base_work_dir(
    source: str, *, working_path: Path | None, database_path: Path | None
) -> Path:
    if database_path is not None:
        resolved = database_path.resolve()
        return resolved if resolved.is_dir() else resolved.parent

    base_dir = working_path.resolve().parent if working_path is not None else Path.cwd()
    for line in source.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        directive = _BASE_DIRECTIVE_RE.match(line)
        if directive is not None:
            raw_value = directive.group("value").strip().strip('"').strip("'")
            configured = Path(raw_value)
            if not configured.is_absolute():
                configured = (base_dir / configured).resolve()
            else:
                configured = configured.resolve()
            return configured if configured.is_dir() else configured.parent
        if not stripped.startswith("*"):
            break
    return base_dir


def _normalize_output(output: str) -> str:
    text = output.rstrip("\n")
    return text if text else "(no output)"
