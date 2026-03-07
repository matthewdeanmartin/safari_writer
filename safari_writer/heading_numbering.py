"""Helpers for Safari Writer section heading auto-numbering."""

from __future__ import annotations


def next_heading_number(counters: list[int], level: int) -> str:
    """Advance heading counters and return the formatted outline number."""
    level = max(1, min(level, 9))

    while len(counters) < level:
        counters.append(0)
    del counters[level:]

    if level > 1 and counters and counters[0] == 0:
        counters[0] = 1

    counters[level - 1] += 1

    if level == 1:
        return f"{counters[0]}.0"
    return ".".join(str(part) for part in counters)
