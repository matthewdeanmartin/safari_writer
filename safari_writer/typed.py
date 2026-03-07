"""Shared typing helpers for Safari Writer."""

from __future__ import annotations

from typing import Protocol, TypeAlias, TypedDict

__all__ = [
    "MailMergeData",
    "MailMergeFieldData",
    "MailMergeFieldInfo",
    "MailMergeInspectInfo",
    "SpellChecker",
    "WordMatch",
]


WordMatch: TypeAlias = tuple[int, int, str]


class SpellChecker(Protocol):
    """Protocol for spell-check engines used by the proofing helpers."""

    def check(self, word: str) -> bool: ...

    def suggest(self, word: str) -> list[str]: ...


class MailMergeFieldData(TypedDict):
    name: str
    max_len: int


class MailMergeData(TypedDict):
    fields: list[MailMergeFieldData]
    records: list[list[str]]


class MailMergeFieldInfo(TypedDict):
    index: int
    name: str
    max_len: int


class MailMergeInspectInfo(TypedDict):
    filename: str
    record_count: int
    records_free: int
    field_count: int
    fields: list[MailMergeFieldInfo]
