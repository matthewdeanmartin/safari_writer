"""Property-based tests for non-UI Safari Fed client helpers."""

from __future__ import annotations

import string
from datetime import timedelta, timezone

from hypothesis import given
from hypothesis import strategies as st

from safari_fed.client import SafariFedClient

HTML_TEXT = st.text(
    alphabet=string.ascii_letters + string.digits + " .,_-",
    min_size=1,
    max_size=20,
).filter(lambda value: value.strip() != "")
UTC_OFFSETS = st.builds(
    timezone,
    st.timedeltas(
        min_value=timedelta(hours=-23),
        max_value=timedelta(hours=23),
    ),
)


def _client() -> SafariFedClient:
    return SafariFedClient.__new__(SafariFedClient)


@given(st.lists(HTML_TEXT, min_size=1, max_size=5))
def test_plain_text_removes_tags_and_unescapes_entities(fragments: list[str]) -> None:
    html = (
        "<p>"
        + "</p><br><p>".join(f"{fragment} &amp; {fragment}" for fragment in fragments)
        + "</p>"
    )

    result = _client()._plain_text(html)
    expected = [f"{fragment} & {fragment}" for fragment in fragments]
    expected[0] = expected[0].lstrip()
    expected[-1] = expected[-1].rstrip()

    assert [line for line in result.splitlines() if line] == expected
    assert "<" not in result
    assert ">" not in result


@given(st.datetimes())
def test_parse_datetime_treats_naive_iso_strings_as_utc(value) -> None:
    parsed = _client()._parse_datetime(value.isoformat())

    assert parsed == value.replace(tzinfo=timezone.utc)


@given(st.datetimes(timezones=UTC_OFFSETS))
def test_parse_datetime_normalizes_aware_iso_strings_to_utc(value) -> None:
    parsed = _client()._parse_datetime(value.isoformat())

    assert parsed == value.astimezone(timezone.utc)
    assert parsed.tzinfo == timezone.utc
