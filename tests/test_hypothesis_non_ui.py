"""Property-based tests for non-UI Safari Writer helpers."""

from __future__ import annotations

import re
import string
import tempfile
from pathlib import Path

from hypothesis import given
from hypothesis import strategies as st

from safari_writer.format_codec import (
    decode_sfw,
    encode_sfw,
    has_controls,
    strip_controls,
)
from safari_writer.heading_numbering import next_heading_number
from safari_writer.mail_merge_db import (
    MAX_FIELD_DATA_LEN,
    MAX_FIELD_NAME_LEN,
    MAX_FIELDS,
    FieldDef,
    MailMergeDB,
    apply_mail_merge_to_buffer,
    validate_mail_merge_data,
)
from safari_writer.proofing import check_word, extract_words, load_personal_dictionary

CONTROL_CHARS = "".join(
    chr(code) for code in (1, 2, 3, 4, 5, 6, 7, 16, 17, 18, 19, 20, 21, 22, 23)
)
PUNCTUATION = ".,;:!?\"'()-"
SAFE_CHARS = st.characters(blacklist_characters="\n\r", blacklist_categories=("Cs",))
LINE_TEXT = st.text(alphabet=SAFE_CHARS, max_size=40)
BUFFER_TEXT = st.lists(LINE_TEXT, min_size=1, max_size=8)
NAME_TEXT = st.text(
    alphabet=string.ascii_letters + string.digits + " _-",
    min_size=1,
    max_size=MAX_FIELD_NAME_LEN,
).filter(lambda value: value.strip() != "")
VALUE_TEXT = st.text(
    alphabet=st.characters(
        blacklist_characters="\n\r\x11",
        blacklist_categories=("Cs",),
    ),
    max_size=MAX_FIELD_DATA_LEN,
)
MERGE_LITERAL_TEXT = st.text(
    alphabet=SAFE_CHARS.filter(lambda ch: ch != "\x11" and not ch.isdigit()),
    max_size=10,
)


class RecordingChecker:
    """Test checker that records lookup requests."""

    def __init__(self, result: bool):
        self.result = result
        self.calls: list[str] = []

    def check(self, word: str) -> bool:
        self.calls.append(word)
        return self.result


@st.composite
def valid_mail_merge_data(draw: st.DrawFn) -> dict[str, object]:
    field_count = draw(st.integers(min_value=1, max_value=MAX_FIELDS))
    fields: list[dict[str, object]] = []
    max_lens: list[int] = []
    for _ in range(field_count):
        name = draw(NAME_TEXT)
        max_len = draw(st.integers(min_value=1, max_value=MAX_FIELD_DATA_LEN))
        fields.append({"name": name, "max_len": max_len})
        max_lens.append(max_len)

    record_count = draw(st.integers(min_value=0, max_value=12))
    records: list[list[str]] = []
    for _ in range(record_count):
        records.append(
            [
                draw(st.text(alphabet=SAFE_CHARS, max_size=max_len))
                for max_len in max_lens
            ]
        )

    return {"fields": fields, "records": records}


@st.composite
def merge_case(draw: st.DrawFn) -> tuple[list[str], MailMergeDB, list[str]]:
    field_count = draw(st.integers(min_value=1, max_value=5))
    fields: list[FieldDef] = []
    record: list[str] = []
    for index in range(field_count):
        max_len = draw(st.integers(min_value=1, max_value=MAX_FIELD_DATA_LEN))
        fields.append(FieldDef(f"Field{index + 1}", max_len))
        record.append(
            draw(
                st.text(
                    alphabet=SAFE_CHARS.filter(lambda ch: ch != "\x11"),
                    max_size=max_len,
                )
            )
        )

    line_count = draw(st.integers(min_value=1, max_value=5))
    buffer: list[str] = []
    expected: list[str] = []

    for _ in range(line_count):
        part_count = draw(st.integers(min_value=0, max_value=6))
        line_parts: list[str] = []
        expected_parts: list[str] = []
        for _ in range(part_count):
            if draw(st.booleans()):
                literal = draw(MERGE_LITERAL_TEXT)
                line_parts.append(literal)
                expected_parts.append(literal)
                continue

            field_number = draw(st.integers(min_value=1, max_value=field_count + 2))
            line_parts.append(f"\x11{field_number}")
            if field_number <= field_count:
                expected_parts.append(record[field_number - 1])
            else:
                expected_parts.append(f"<<@{field_number}>>")

        buffer.append("".join(line_parts))
        expected.append("".join(expected_parts))

    return buffer, MailMergeDB(fields=fields, records=[record]), expected


@st.composite
def punctuated_word(draw: st.DrawFn) -> tuple[str, str]:
    core = draw(st.text(alphabet=string.ascii_letters, min_size=1, max_size=20))
    prefix = draw(st.text(alphabet=PUNCTUATION, max_size=4))
    suffix = draw(st.text(alphabet=PUNCTUATION, max_size=4))
    return f"{prefix}{core}{suffix}", core


@given(BUFFER_TEXT)
def test_format_codec_round_trips_generated_buffers(buffer: list[str]):
    assert decode_sfw(encode_sfw(buffer)) == buffer


@given(BUFFER_TEXT)
def test_strip_controls_is_idempotent_and_clears_known_controls(buffer: list[str]):
    stripped = strip_controls(buffer)

    assert strip_controls(stripped) == stripped
    assert has_controls(stripped) is False
    assert has_controls(buffer) is any(
        ch in CONTROL_CHARS for line in buffer for ch in line
    )


@given(st.lists(st.integers(min_value=-5, max_value=20), min_size=1, max_size=30))
def test_heading_numbering_is_deterministic(levels: list[int]):
    counters_a: list[int] = []
    counters_b: list[int] = []

    outputs_a = [next_heading_number(counters_a, level) for level in levels]
    outputs_b = [next_heading_number(counters_b, level) for level in levels]

    assert outputs_a == outputs_b
    assert counters_a == counters_b


@given(
    st.lists(st.integers(min_value=0, max_value=10), max_size=12),
    st.integers(min_value=-5, max_value=20),
)
def test_heading_numbering_matches_mutated_counter_shape(
    initial: list[int], level: int
):
    counters = initial.copy()
    result = next_heading_number(counters, level)
    effective_level = max(1, min(level, 9))

    assert re.fullmatch(r"\d+(?:\.\d+)+", result)
    if effective_level == 1:
        assert counters == [int(result.split(".")[0])]
        assert result.endswith(".0")
        return

    assert len(counters) == effective_level
    assert result.split(".") == [str(part) for part in counters]


@given(valid_mail_merge_data())
def test_valid_mail_merge_data_round_trips_through_db(data: dict[str, object]):
    assert validate_mail_merge_data(data) == []

    restored = MailMergeDB.from_dict(data)
    assert restored.to_dict() == data


@given(st.lists(VALUE_TEXT, max_size=20), VALUE_TEXT, VALUE_TEXT)
def test_apply_subset_matches_case_insensitive_range(
    values: list[str], low: str, high: str
):
    db = MailMergeDB(
        fields=[FieldDef("State", MAX_FIELD_DATA_LEN)],
        records=[[value] for value in values],
    )

    expected = [
        index
        for index, value in enumerate(values)
        if low.lower() <= value.lower() <= high.lower()
    ]
    assert db.apply_subset(0, low, high) == expected


@given(merge_case())
def test_apply_mail_merge_replaces_markers_and_is_idempotent(
    case: tuple[list[str], MailMergeDB, list[str]],
):
    buffer, db, expected = case

    merged = apply_mail_merge_to_buffer(buffer, db)
    assert merged == expected
    assert apply_mail_merge_to_buffer(merged, db) == merged


@given(BUFFER_TEXT)
def test_extract_words_only_returns_clean_ascii_word_spans(buffer: list[str]):
    matches = extract_words(buffer)

    for row, col, word in matches:
        clean_line = re.sub(r"[\x01-\x1f]", " ", buffer[row])
        assert clean_line[col : col + len(word)] == word
        assert re.fullmatch(r"[A-Za-z']+", word)


@given(punctuated_word(), st.booleans())
def test_check_word_short_circuits_known_word_sets(
    case: tuple[str, str], use_kept: bool
):
    word, core = case
    checker = RecordingChecker(result=False)
    kept = {core.lower()} if use_kept else set()
    personal = set() if use_kept else {core.lower()}

    assert check_word(word, checker, kept, personal) is True
    assert checker.calls == []


@given(punctuated_word())
def test_check_word_passes_stripped_word_to_checker(case: tuple[str, str]):
    word, core = case
    checker = RecordingChecker(result=False)

    assert check_word(word, checker, set(), set()) is False
    assert checker.calls == [core]


@given(
    st.lists(
        st.text(alphabet=string.ascii_letters, min_size=1, max_size=20),
        min_size=1,
        max_size=20,
    )
)
def test_load_personal_dictionary_normalizes_words(words: list[str]):
    with tempfile.TemporaryDirectory() as temp_dir:
        path = Path(temp_dir) / "personal.txt"
        path.write_text(" \n\t ".join(words), encoding="utf-8")

        assert load_personal_dictionary(path) == {word.lower() for word in words}
