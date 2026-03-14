"""Filesystem services for Safari DOS."""

from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
import zipfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Literal

__all__ = [
    "CODE_EXTENSIONS",
    "DeviceLocation",
    "DirectoryEntry",
    "GarbageEntry",
    "copy_paths",
    "create_folder",
    "discover_locations",
    "duplicate_path",
    "format_timestamp",
    "get_entry_info",
    "get_preview_syntax",
    "get_preview_text",
    "list_favorites",
    "list_directory",
    "list_garbage",
    "list_recent_documents",
    "list_recent_locations",
    "move_paths",
    "move_to_garbage",
    "record_recent_document",
    "record_recent_location",
    "rename_path",
    "restore_from_garbage",
    "set_protected",
    "toggle_favorite",
    "unzip_path",
    "zip_paths",
]

# GarbageEntry models items visible in the OS trash / recycling bin.

SORT_FIELDS = ("name", "date", "size", "type")


@dataclass(frozen=True)
class DirectoryEntry:
    """Describe an item visible in a file listing."""

    path: Path
    name: str
    kind: str
    size_bytes: int | None
    modified_at: datetime
    protected: bool
    hidden: bool
    is_dir: bool
    is_link: bool


@dataclass(frozen=True)
class DeviceLocation:
    """Describe a browseable root or shortcut."""

    token: str
    label: str
    path: Path


@dataclass(frozen=True)
class GarbageEntry:
    """Describe an item stored in Safari DOS garbage."""

    item_id: str
    name: str
    stored_path: Path
    original_path: Path
    deleted_at: datetime
    is_dir: bool


def _support_root() -> Path:
    root = os.environ.get("SAFARI_DOS_HOME")
    if root:
        return Path(root)
    return Path.home() / ".safari_dos"


def _favorites_path() -> Path:
    return _support_root() / "favorites.json"


def _recent_locations_path() -> Path:
    return _support_root() / "recent_locations.json"


def _recent_documents_path() -> Path:
    return _support_root() / "recent_documents.json"


def _load_path_list(path: Path) -> list[Path]:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError(f"Path list is invalid: {path}")
    result: list[Path] = []
    seen: set[Path] = set()
    for item in payload:
        candidate = Path(str(item)).resolve()
        if candidate in seen:
            continue
        seen.add(candidate)
        result.append(candidate)
    return result


def _save_path_list(path: Path, values: list[Path]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = [str(value.resolve()) for value in values]
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _is_hidden(path: Path) -> bool:
    if path.name.startswith("."):
        return True
    try:
        path_stat = path.stat()
    except OSError:
        return False
    file_attributes = getattr(path_stat, "st_file_attributes", 0)
    hidden_attribute = getattr(stat, "FILE_ATTRIBUTE_HIDDEN", 0)
    return bool(hidden_attribute and file_attributes & hidden_attribute)


def _is_protected(path: Path) -> bool:
    path_stat = path.stat()
    file_attributes = getattr(path_stat, "st_file_attributes", 0)
    readonly_attribute = getattr(stat, "FILE_ATTRIBUTE_READONLY", 0)
    if readonly_attribute and file_attributes & readonly_attribute:
        return True
    writable_bits = stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH
    return not bool(path_stat.st_mode & writable_bits)


def set_protected(path: Path, protected: bool) -> None:
    """Apply or clear Safari DOS protect semantics on a path."""

    if not path.exists():
        raise FileNotFoundError(f"Path not found: {path}")
    if os.name == "nt":
        readonly_attribute = getattr(stat, "FILE_ATTRIBUTE_READONLY", 0)
        if readonly_attribute:
            import ctypes

            current_attributes = getattr(path.stat(), "st_file_attributes", 0)
            new_attributes = (
                current_attributes | readonly_attribute
                if protected
                else current_attributes & ~readonly_attribute
            )
            result = ctypes.windll.kernel32.SetFileAttributesW(
                str(path),
                int(new_attributes),
            )
            if result == 0:
                error_code = ctypes.get_last_error()
                raise OSError(error_code, f"Unable to update protection for {path}")
            return

    current_mode = path.stat().st_mode
    writable_bits = stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH
    new_mode = (
        current_mode & ~writable_bits if protected else current_mode | stat.S_IWUSR
    )
    path.chmod(new_mode)


def format_timestamp(value: datetime) -> str:
    """Render a timestamp using the user's locale format."""
    from safari_writer.locale_info import format_datetime

    return format_datetime(value, style="short")


def _format_copy_name(path: Path, index: int) -> str:
    if path.is_dir():
        suffix = "" if index == 1 else f" {index}"
        return f"{path.name} COPY{suffix}"
    stem = path.stem
    extension = path.suffix
    suffix = "" if index == 1 else f" {index}"
    return f"{stem} COPY{suffix}{extension}"


def _directory_sort_key(entry: DirectoryEntry, sort_field: str) -> tuple[object, ...]:
    common = (not entry.is_dir,)
    if sort_field == "date":
        return common + (-entry.modified_at.timestamp(), entry.name.lower())
    if sort_field == "size":
        return common + (-(entry.size_bytes or 0), entry.name.lower())
    if sort_field == "type":
        return common + (entry.kind.lower(), entry.name.lower())
    return common + (entry.name.lower(),)


def list_directory(
    directory: Path,
    *,
    show_hidden: bool = False,
    filter_text: str = "",
    sort_field: str = "name",
    ascending: bool = True,
) -> list[DirectoryEntry]:
    """List a directory with Safari DOS metadata."""

    if sort_field not in SORT_FIELDS:
        raise ValueError(f"Unsupported sort field: {sort_field}")
    if not directory.exists():
        raise FileNotFoundError(f"Path not found: {directory}")
    if not directory.is_dir():
        raise NotADirectoryError(f"Not a directory: {directory}")

    lowered_filter = filter_text.lower()
    entries: list[DirectoryEntry] = []
    for item in directory.iterdir():
        hidden = _is_hidden(item)
        if hidden and not show_hidden:
            continue
        if lowered_filter and lowered_filter not in item.name.lower():
            continue
        item_stat = item.stat()
        is_dir = item.is_dir()
        kind = (
            "<DIR>" if is_dir else (item.suffix[1:].upper() if item.suffix else "FILE")
        )
        entries.append(
            DirectoryEntry(
                path=item,
                name=item.name,
                kind=kind,
                size_bytes=None if is_dir else item_stat.st_size,
                modified_at=datetime.fromtimestamp(item_stat.st_mtime),
                protected=_is_protected(item),
                hidden=hidden,
                is_dir=is_dir,
                is_link=item.is_symlink(),
            )
        )

    entries.sort(key=lambda entry: _directory_sort_key(entry, sort_field))
    if not ascending:
        dirs = [entry for entry in entries if entry.is_dir]
        files = [entry for entry in entries if not entry.is_dir]
        dirs.reverse()
        files.reverse()
        entries = dirs + files
    return entries


def list_favorites() -> list[Path]:
    """Return configured favorite locations."""

    return [path for path in _load_path_list(_favorites_path()) if path.exists()]


def toggle_favorite(path: Path) -> bool:
    """Add or remove a favorite location. Returns True when added."""

    target = path.resolve()
    favorites = list_favorites()
    if target in favorites:
        favorites = [favorite for favorite in favorites if favorite != target]
        _save_path_list(_favorites_path(), favorites)
        return False
    favorites.append(target)
    favorites.sort(key=lambda value: value.as_posix().lower())
    _save_path_list(_favorites_path(), favorites)
    return True


def _record_recent(path: Path, storage_path: Path, *, limit: int = 10) -> list[Path]:
    target = path.resolve()
    values = [target]
    values.extend(
        existing for existing in _load_path_list(storage_path) if existing != target
    )
    trimmed = values[:limit]
    _save_path_list(storage_path, trimmed)
    return [value for value in trimmed if value.exists()]


def list_recent_locations() -> list[Path]:
    """Return recent folders used in Safari DOS or Writer handoffs."""

    return [path for path in _load_path_list(_recent_locations_path()) if path.exists()]


def record_recent_location(path: Path, *, limit: int = 10) -> list[Path]:
    """Record a location for later quick access."""

    return _record_recent(path, _recent_locations_path(), limit=limit)


def list_recent_documents() -> list[Path]:
    """Return recent writer documents shared with Safari DOS."""

    return [path for path in _load_path_list(_recent_documents_path()) if path.exists()]


def record_recent_document(path: Path, *, limit: int = 10) -> list[Path]:
    """Record a writer document for Safari DOS handoff screens."""

    return _record_recent(path, _recent_documents_path(), limit=limit)


def create_folder(parent: Path, name: str) -> Path:
    """Create a new folder beneath ``parent``."""

    clean_name = name.strip()
    if not clean_name:
        raise ValueError("Folder name cannot be empty")
    destination = parent / clean_name
    destination.mkdir()
    return destination


def rename_path(source: Path, new_name: str) -> Path:
    """Rename a file or folder in place."""

    clean_name = new_name.strip()
    if not clean_name:
        raise ValueError("New name cannot be empty")
    destination = source.with_name(clean_name)
    if destination.exists():
        raise FileExistsError(f"Name already exists: {destination}")
    source.rename(destination)
    return destination


def duplicate_path(source: Path) -> Path:
    """Duplicate a file or folder beside the source."""

    for index in range(1, 10_000):
        candidate = source.with_name(_format_copy_name(source, index))
        if candidate.exists():
            continue
        if source.is_dir():
            shutil.copytree(source, candidate, copy_function=shutil.copy2)
        else:
            shutil.copy2(source, candidate)
        return candidate
    raise OSError(f"Unable to find duplicate name for {source}")


def _copy_one(source: Path, destination_dir: Path) -> Path:
    destination = destination_dir / source.name
    if destination.exists():
        raise FileExistsError(f"Name already exists: {destination}")
    if source.is_dir():
        shutil.copytree(source, destination, copy_function=shutil.copy2)
    else:
        shutil.copy2(source, destination)
    return destination


def copy_paths(paths: list[Path], destination_dir: Path) -> list[Path]:
    """Copy one or more items into ``destination_dir``."""

    if not destination_dir.is_dir():
        raise NotADirectoryError(f"Destination is not a directory: {destination_dir}")
    return [_copy_one(path, destination_dir) for path in paths]


def _move_one(source: Path, destination_dir: Path) -> Path:
    destination = destination_dir / source.name
    if destination.exists():
        raise FileExistsError(f"Name already exists: {destination}")
    return Path(shutil.move(str(source), str(destination)))


def move_paths(paths: list[Path], destination_dir: Path) -> list[Path]:
    """Move one or more items into ``destination_dir``."""

    if not destination_dir.is_dir():
        raise NotADirectoryError(f"Destination is not a directory: {destination_dir}")
    return [_move_one(path, destination_dir) for path in paths]


def move_to_garbage(path: Path) -> GarbageEntry:
    """Send an item to the OS trash / recycling bin via send2trash."""

    if not path.exists():
        raise FileNotFoundError(f"Path not found: {path}")
    from send2trash import send2trash

    deleted_at = datetime.now()
    is_dir = path.is_dir()
    send2trash(str(path))
    return GarbageEntry(
        item_id="",
        name=path.name,
        stored_path=path,
        original_path=path,
        deleted_at=deleted_at,
        is_dir=is_dir,
    )


def _parse_recycle_deleted_at(raw_value: object) -> datetime:
    if isinstance(raw_value, (int, float)):
        return datetime.fromtimestamp(raw_value)
    if isinstance(raw_value, str):
        raw_text = raw_value.strip()
        if raw_text:
            try:
                return datetime.fromisoformat(raw_text.replace("Z", "+00:00"))
            except ValueError:
                pass
    return datetime.fromtimestamp(0)


def _list_windows_garbage() -> list[GarbageEntry]:
    script = r"""
$ErrorActionPreference = 'Stop'
$shell = New-Object -ComObject Shell.Application
$bin = $shell.Namespace(0xA)
if ($null -eq $bin) {
    @() | ConvertTo-Json -Compress
    exit 0
}
$items = foreach ($item in $bin.Items()) {
    $deletedAt = $item.ExtendedProperty('System.Recycle.DateDeleted')
    [PSCustomObject]@{
        ItemId = [string]$item.Path
        Name = [string]$item.Name
        OriginalPath = [string]$item.ExtendedProperty('System.Recycle.DeletedFrom')
        DeletedAt = if ($deletedAt -is [DateTime]) { $deletedAt.ToString('o') } else { [string]$deletedAt }
        IsDir = [bool]$item.IsFolder
    }
}
$items | ConvertTo-Json -Compress
"""
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", script],
            capture_output=True,
            text=True,
            check=True,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise OSError("Unable to query the Windows Recycle Bin") from exc

    payload_text = result.stdout.strip()
    if not payload_text:
        return []
    payload = json.loads(payload_text)
    items = payload if isinstance(payload, list) else [payload]
    entries: list[GarbageEntry] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        original_raw = str(item.get("OriginalPath") or "").strip()
        original_path = Path(original_raw) if original_raw else Path(
            str(item.get("Name") or item.get("ItemId") or "recycled-item")
        )
        name = str(item.get("Name") or original_path.name or original_path)
        entries.append(
            GarbageEntry(
                item_id=str(item.get("ItemId") or original_path),
                name=name,
                stored_path=original_path,
                original_path=original_path,
                deleted_at=_parse_recycle_deleted_at(item.get("DeletedAt")),
                is_dir=bool(item.get("IsDir", False)),
            )
        )
    entries.sort(key=lambda entry: entry.deleted_at, reverse=True)
    return entries


def list_garbage() -> list[GarbageEntry]:
    """Return items currently visible in the OS trash / recycling bin."""

    if os.name != "nt":
        return []
    return _list_windows_garbage()


def restore_from_garbage(item_id: str, destination: Path | None = None) -> Path:
    """Restore a garbage item. Not supported when using the OS trash."""

    raise FileNotFoundError(f"Garbage item not found: {item_id}")


def get_entry_info(path: Path) -> str:
    """Return a plain-language item summary."""

    if not path.exists():
        raise FileNotFoundError(f"Path not found: {path}")
    item_stat = path.stat()
    lines = [
        f"Name: {path.name}",
        f"Path: {path}",
        f"Type: {'Folder' if path.is_dir() else 'File'}",
        f"Modified: {format_timestamp(datetime.fromtimestamp(item_stat.st_mtime))}",
        f"Protected: {'Yes' if _is_protected(path) else 'No'}",
    ]
    if path.is_dir():
        try:
            item_count = sum(1 for _ in path.iterdir())
            lines.append(f"Items: {item_count}")
        except PermissionError:
            lines.append("Items: (access denied)")
    else:
        lines.append(f"Size: {item_stat.st_size:,} bytes")
    return "\n".join(lines)


def discover_locations(current_path: Path | None = None) -> list[DeviceLocation]:
    """Discover useful browseable locations."""

    locations: list[tuple[str, Path]] = []
    if current_path is not None:
        current_root = current_path.anchor or str(current_path)
        locations.append(("Current Drive", Path(current_root)))

    home = Path.home()
    standard = [
        ("Home", home),
        ("Documents", home / "Documents"),
        ("Downloads", home / "Downloads"),
        ("Desktop", home / "Desktop"),
    ]
    for label, path in standard:
        if path.exists():
            locations.append((label, path))
    for favorite in list_favorites():
        if favorite.exists():
            locations.append((f"Favorite: {favorite.name or favorite.drive}", favorite))

    if os.name == "nt":
        try:
            import ctypes

            bitmask = ctypes.windll.kernel32.GetLogicalDrives()
        except AttributeError:
            bitmask = 0
        for index in range(26):
            if not bitmask & (1 << index):
                continue
            letter = chr(65 + index)
            drive = Path(f"{letter}:\\")
            if drive.exists():
                locations.append((f"Drive {letter}", drive))
    else:
        for label, base in [
            ("Root", Path("/")),
            ("Volumes", Path("/Volumes")),
            ("Media", Path("/media")),
            ("Mounts", Path("/mnt")),
        ]:
            if base.exists():
                if base == Path("/"):
                    locations.append((label, base))
                else:
                    for child in sorted(base.iterdir()):
                        if child.is_dir():
                            locations.append((child.name, child))

    seen: set[Path] = set()
    result: list[DeviceLocation] = []
    for position, (label, path) in enumerate(locations, start=1):
        resolved = path.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        result.append(DeviceLocation(token=str(position), label=label, path=resolved))
    return result


CODE_EXTENSIONS: frozenset[str] = frozenset(
    {
        # BASIC variants
        ".bas",
        ".vb",
        ".vbs",
        # C family
        ".c",
        ".h",
        ".cpp",
        ".cc",
        ".cxx",
        ".hpp",
        ".hxx",
        ".cs",
        # JVM
        ".java",
        ".kt",
        ".kts",
        ".groovy",
        ".gradle",
        ".scala",
        # Web
        ".js",
        ".mjs",
        ".cjs",
        ".jsx",
        ".ts",
        ".tsx",
        ".html",
        ".htm",
        ".css",
        ".scss",
        ".sass",
        ".vue",
        ".coffee",
        # Scripting
        ".py",
        ".rb",
        ".pl",
        ".pm",
        ".php",
        ".lua",
        ".tcl",
        # Shell
        ".sh",
        ".bash",
        ".zsh",
        ".fish",
        ".ps1",
        ".bat",
        ".cmd",
        # Systems
        ".rs",
        ".go",
        ".d",
        ".nim",
        ".zig",
        ".v",
        # Assembly
        ".asm",
        ".s",
        # Functional / academic
        ".hs",
        ".lhs",
        ".ml",
        ".mli",
        ".fs",
        ".fsx",
        ".fsi",
        ".clj",
        ".cljs",
        ".lisp",
        ".scm",
        ".rkt",
        ".ex",
        ".exs",
        ".erl",
        ".hrl",
        # Mobile / other
        ".swift",
        ".dart",
        ".m",
        ".mm",
        # Data science
        ".r",
        ".jl",
        ".f",
        ".f90",
        ".for",
        # Infrastructure / config-as-code
        ".tf",
        ".hcl",
        # Data / markup (preview-worthy as code)
        ".json",
        ".toml",
        ".yaml",
        ".yml",
        ".xml",
        ".sql",
        # Misc text formats already previewed
        ".txt",
        ".md",
        ".rst",
        ".ini",
        ".cfg",
        ".conf",
        ".sfw",
    }
)


def get_preview_text(path: Path, limit_lines: int = 25) -> str:
    """Read the first few lines of a file for preview."""

    if not path.exists() or path.is_dir():
        return ""
    try:
        # Read a small chunk first to avoid loading huge files
        with path.open("r", encoding="utf-8", errors="replace") as f:
            lines = []
            for _ in range(limit_lines):
                line = f.readline()
                if not line:
                    break
                lines.append(line.rstrip())
            return "\n".join(lines)
    except Exception as exc:
        return f"Error reading preview: {exc}"


def get_preview_syntax(path: Path, limit_lines: int = 25) -> object:
    """Return a Rich Syntax renderable for ``path``, or a plain string on failure.

    Falls back to plain text for files without a recognised Pygments lexer, and
    returns a plain error string if the file cannot be read.
    """

    text = get_preview_text(path, limit_lines=limit_lines)
    if text.startswith("Error reading preview:") or not text:
        return text

    from rich.syntax import Syntax

    try:
        from pygments.lexers import get_lexer_for_filename
        from pygments.util import ClassNotFound

        try:
            get_lexer_for_filename(path.name)
            lexer = path.suffix.lstrip(".") or "text"
        except ClassNotFound:
            lexer = "text"
    except ImportError:
        lexer = "text"

    return Syntax(
        text,
        lexer,
        theme="monokai",
        line_numbers=True,
        word_wrap=False,
    )


def zip_paths(
    paths: list[Path], archive_path: Path, mode: Literal["w", "a", "x"] = "w"
) -> Path:
    """Create or append to a ZIP archive."""

    # Ensure archive name has .zip
    if archive_path.suffix.lower() != ".zip":
        archive_path = archive_path.with_suffix(".zip")

    with zipfile.ZipFile(archive_path, mode, zipfile.ZIP_DEFLATED) as zf:
        for path in paths:
            if not path.exists():
                continue
            if path.is_dir():
                # Add the directory itself and all its contents
                for root, _, files in os.walk(path):
                    rel_root = Path(root).relative_to(path.parent)
                    zf.write(root, str(rel_root))
                    for file in files:
                        file_path = Path(root) / file
                        arcname = file_path.relative_to(path.parent)
                        zf.write(file_path, str(arcname))
            else:
                zf.write(path, path.name)
    return archive_path


def unzip_path(archive_path: Path, destination_dir: Path) -> None:
    """Extract a ZIP archive to a destination directory."""

    if not archive_path.exists():
        raise FileNotFoundError(f"Archive not found: {archive_path}")
    if not zipfile.is_zipfile(archive_path):
        raise ValueError(f"Not a valid ZIP file: {archive_path}")

    with zipfile.ZipFile(archive_path, "r") as zf:
        zf.extractall(destination_dir)
