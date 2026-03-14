"""Property-based tests for non-UI Safari DOS services."""

from __future__ import annotations

import shutil
import string
from datetime import datetime
from pathlib import Path

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from safari_dos.services import (
    DirectoryEntry,
    _directory_sort_key,
    _format_copy_name,
    format_timestamp,
)

PATH_TEXT = st.text(
    alphabet=string.ascii_letters + string.digits + "_-",
    min_size=1,
    max_size=12,
)


def _entry(name: str, *, is_dir: bool, modified_at: datetime) -> DirectoryEntry:
    return DirectoryEntry(
        path=Path(name),
        name=name,
        kind="<DIR>" if is_dir else "TXT",
        size_bytes=None if is_dir else len(name),
        modified_at=modified_at,
        protected=False,
        hidden=False,
        is_dir=is_dir,
        is_link=False,
    )


@given(st.datetimes(min_value=datetime(1980, 1, 1), max_value=datetime(2100, 1, 1)))
def test_format_timestamp_returns_non_empty_text(value: datetime) -> None:
    rendered = format_timestamp(value)

    assert isinstance(rendered, str)
    assert rendered.strip() != ""


@given(
    PATH_TEXT,
    st.datetimes(min_value=datetime(1980, 1, 1), max_value=datetime(2100, 1, 1)),
    st.sampled_from(["name", "date", "size", "type"]),
)
def test_directory_sort_key_keeps_directories_before_files(
    name: str, modified_at: datetime, sort_field: str
) -> None:
    directory = _entry(name, is_dir=True, modified_at=modified_at)
    file_entry = _entry(name, is_dir=False, modified_at=modified_at)

    assert _directory_sort_key(directory, sort_field) < _directory_sort_key(
        file_entry, sort_field
    )


@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(base_name=PATH_TEXT, index=st.integers(min_value=1, max_value=9))
def test_format_copy_name_preserves_file_suffix(
    tmp_path: Path, base_name: str, index: int
) -> None:
    path = tmp_path / f"{base_name}.txt"
    if path.exists():
        path.unlink()
    path.write_text(base_name, encoding="utf-8")

    rendered = _format_copy_name(path, index)

    assert rendered.endswith(".txt")
    assert "COPY" in rendered
    if index == 1:
        assert rendered == f"{base_name} COPY.txt"
    else:
        assert rendered == f"{base_name} COPY {index}.txt"


@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(folder_name=PATH_TEXT, index=st.integers(min_value=1, max_value=9))
def test_format_copy_name_for_directories_omits_file_extension(
    tmp_path: Path, folder_name: str, index: int
) -> None:
    path = tmp_path / folder_name
    if path.exists():
        shutil.rmtree(path)
    path.mkdir()

    rendered = _format_copy_name(path, index)

    assert rendered.startswith(f"{folder_name} COPY")
    assert "." not in rendered
    if index == 1:
        assert rendered == f"{folder_name} COPY"
    else:
        assert rendered == f"{folder_name} COPY {index}"
