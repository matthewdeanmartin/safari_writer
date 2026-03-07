"""Public interface for Safari DOS."""

from safari_dos.app import SafariDosApp
from safari_dos.main import build_parser, main, parse_args
from safari_dos.services import (
    DeviceLocation,
    DirectoryEntry,
    GarbageEntry,
    create_folder,
    discover_locations,
    duplicate_path,
    format_timestamp,
    list_directory,
    list_garbage,
    move_to_garbage,
    rename_path,
    restore_from_garbage,
)
from safari_dos.state import SafariDosExitRequest, SafariDosState

__all__ = [
    "DeviceLocation",
    "DirectoryEntry",
    "GarbageEntry",
    "SafariDosApp",
    "SafariDosExitRequest",
    "SafariDosState",
    "build_parser",
    "create_folder",
    "discover_locations",
    "duplicate_path",
    "format_timestamp",
    "list_directory",
    "list_garbage",
    "main",
    "move_to_garbage",
    "parse_args",
    "rename_path",
    "restore_from_garbage",
]
