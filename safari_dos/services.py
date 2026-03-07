"""Filesystem services for Safari DOS."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
import os
from pathlib import Path
import shutil
import stat
from typing import Any
from uuid import uuid4

__all__ = [
    "DeviceLocation",
    "DirectoryEntry",
    "GarbageEntry",
    "copy_paths",
    "create_folder",
    "discover_locations",
    "duplicate_path",
    "format_timestamp",
    "get_entry_info",
    "list_directory",
    "list_garbage",
    "move_paths",
    "move_to_garbage",
    "rename_path",
    "restore_from_garbage",
]

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


def _garbage_root() -> Path:
    return _support_root() / "garbage"


def _garbage_items_dir() -> Path:
    return _garbage_root() / "items"


def _garbage_index_path() -> Path:
    return _garbage_root() / "index.json"


def _ensure_garbage_store() -> None:
    _garbage_items_dir().mkdir(parents=True, exist_ok=True)
    index_path = _garbage_index_path()
    if not index_path.exists():
        index_path.write_text("[]", encoding="utf-8")


def _load_garbage_index() -> list[dict[str, Any]]:
    _ensure_garbage_store()
    raw = _garbage_index_path().read_text(encoding="utf-8")
    payload = json.loads(raw)
    if not isinstance(payload, list):
        raise ValueError("Garbage index is invalid")
    return payload


def _save_garbage_index(items: list[dict[str, Any]]) -> None:
    _ensure_garbage_store()
    _garbage_index_path().write_text(
        json.dumps(items, indent=2, sort_keys=True),
        encoding="utf-8",
    )


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
    return not os.access(path, os.W_OK)


def format_timestamp(value: datetime) -> str:
    """Render a timestamp using a stable Atari-like format."""

    return value.strftime("%Y-%m-%d %H:%M")


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
        kind = "<DIR>" if is_dir else (item.suffix[1:].upper() if item.suffix else "FILE")
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
    """Move an item into the Safari DOS garbage store."""

    if not path.exists():
        raise FileNotFoundError(f"Path not found: {path}")
    _ensure_garbage_store()

    item_id = uuid4().hex
    item_dir = _garbage_items_dir() / item_id
    item_dir.mkdir(parents=True, exist_ok=False)
    stored_path = item_dir / path.name
    shutil.move(str(path), str(stored_path))

    deleted_at = datetime.now()
    record = {
        "deleted_at": deleted_at.isoformat(),
        "id": item_id,
        "is_dir": stored_path.is_dir(),
        "name": path.name,
        "original_path": str(path),
        "stored_path": str(stored_path),
    }
    items = _load_garbage_index()
    items.append(record)
    _save_garbage_index(items)
    return GarbageEntry(
        item_id=item_id,
        name=path.name,
        stored_path=stored_path,
        original_path=path,
        deleted_at=deleted_at,
        is_dir=stored_path.is_dir(),
    )


def list_garbage() -> list[GarbageEntry]:
    """Return items currently stored in Safari DOS garbage."""

    entries: list[GarbageEntry] = []
    for item in _load_garbage_index():
        stored_path = Path(item["stored_path"])
        if not stored_path.exists():
            continue
        entries.append(
            GarbageEntry(
                item_id=str(item["id"]),
                name=str(item["name"]),
                stored_path=stored_path,
                original_path=Path(str(item["original_path"])),
                deleted_at=datetime.fromisoformat(str(item["deleted_at"])),
                is_dir=bool(item["is_dir"]),
            )
        )
    entries.sort(key=lambda entry: entry.deleted_at, reverse=True)
    return entries


def restore_from_garbage(item_id: str, destination: Path | None = None) -> Path:
    """Restore a garbage item to its original or alternate location."""

    items = _load_garbage_index()
    for index, item in enumerate(items):
        if item["id"] != item_id:
            continue
        stored_path = Path(str(item["stored_path"]))
        target = Path(destination) if destination is not None else Path(str(item["original_path"]))
        if target.exists():
            raise FileExistsError(f"Name already exists: {target}")
        target.parent.mkdir(parents=True, exist_ok=True)
        restored = Path(shutil.move(str(stored_path), str(target)))
        item_dir = stored_path.parent
        if item_dir.exists():
            item_dir.rmdir()
        items.pop(index)
        _save_garbage_index(items)
        return restored
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
        item_count = sum(1 for _ in path.iterdir())
        lines.append(f"Items: {item_count}")
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

    if os.name == "nt":
        try:
            import ctypes

            bitmask = ctypes.windll.kernel32.GetLogicalDrives()  # type: ignore[attr-defined]
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
        for label, base in [("Root", Path("/")), ("Volumes", Path("/Volumes")), ("Media", Path("/media")), ("Mounts", Path("/mnt"))]:
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
