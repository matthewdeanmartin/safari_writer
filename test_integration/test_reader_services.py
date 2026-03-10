"""Integration tests for Safari Reader services.

Run all tests:         uv run pytest test_integration/ -v
Run only offline:      uv run pytest test_integration/ -v -m "not live"
Run only live:         uv run pytest test_integration/ -v -m live
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from safari_reader.services import (
    add_book_to_library,
    delete_book,
    download_gutenberg_text,
    format_book_text,
    gutenberg_book_detail,
    import_local_file,
    load_library,
    load_reading_state,
    open_book,
    parse_chapters,
    save_library,
    save_reading_state,
    search_gutenberg,
    strip_html_tags,
    top_gutenberg,
)
from safari_reader.state import (
    BookMeta,
    Bookmark,
    ReaderSettings,
    SafariReaderState,
)


# ── Offline unit-level tests (no network) ────────────────────────


class TestStripHtml:
    def test_simple_tags(self) -> None:
        assert "Hello world" in strip_html_tags("<p>Hello <b>world</b></p>")

    def test_script_removed(self) -> None:
        result = strip_html_tags("<script>alert(1)</script>visible")
        assert "alert" not in result
        assert "visible" in result

    def test_br_becomes_newline(self) -> None:
        result = strip_html_tags("line1<br>line2")
        assert "\n" in result

    def test_empty_input(self) -> None:
        assert strip_html_tags("") == ""

    def test_plain_text_passthrough(self) -> None:
        assert strip_html_tags("no tags here") == "no tags here"


class TestParseChapters:
    def test_finds_chapters(self) -> None:
        text = "Intro\n\nCHAPTER I. First\n\ntext\n\nCHAPTER II. Second\n\nmore"
        chapters = parse_chapters(text)
        assert len(chapters) == 2
        assert "CHAPTER I" in chapters[0][0]
        assert "CHAPTER II" in chapters[1][0]
        assert chapters[0][1] < chapters[1][1]

    def test_no_chapters_returns_beginning(self) -> None:
        chapters = parse_chapters("Just some text without chapters.")
        assert len(chapters) == 1
        assert chapters[0] == ("Beginning", 0)

    def test_mixed_case_headings(self) -> None:
        text = "Chapter 1. Abc\n\nChapter 2. Def"
        chapters = parse_chapters(text)
        assert len(chapters) == 2

    def test_book_and_part_headings(self) -> None:
        text = "BOOK I\n\ntext\n\nPART TWO\n\nmore"
        chapters = parse_chapters(text)
        assert len(chapters) == 2


class TestFormatBookText:
    def test_basic_wrapping(self) -> None:
        text = "word " * 30
        result = format_book_text(text, width=60, margin=4)
        for line in result.split("\n"):
            if line.strip():
                assert line.startswith("    ")
                assert len(line) <= 60

    def test_paragraph_separation(self) -> None:
        text = "para one\n\npara two"
        result = format_book_text(text, width=80, margin=2)
        assert "\n\n" in result or "\n \n" in result

    def test_narrow_width_still_works(self) -> None:
        result = format_book_text("Hello world", width=20, margin=0)
        assert "Hello" in result


class TestLibraryPersistence:
    def test_save_and_load_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            state = SafariReaderState(library_dir=Path(td))
            state.library = [
                BookMeta(
                    title="Test Book",
                    author="Author",
                    source="local",
                    file_path=Path(td) / "test.txt",
                ),
            ]
            save_library(state)

            state2 = SafariReaderState(library_dir=Path(td))
            load_library(state2)
            assert len(state2.library) == 1
            assert state2.library[0].title == "Test Book"
            assert state2.library[0].author == "Author"

    def test_load_missing_index(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            state = SafariReaderState(library_dir=Path(td))
            load_library(state)
            assert state.library == []

    def test_load_corrupt_index(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            (Path(td) / "_index.json").write_text("NOT JSON", encoding="utf-8")
            state = SafariReaderState(library_dir=Path(td))
            load_library(state)
            assert state.library == []


class TestReadingState:
    def test_save_and_load_bookmarks(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            state = SafariReaderState(library_dir=Path(td))
            state.current_book = BookMeta(title="BM Test", source_id="pg999")
            state.current_position = 1234
            state.bookmarks = [
                Bookmark(name="Mark 1", position=500, chapter="Ch1", excerpt="hello"),
            ]
            save_reading_state(state)

            state2 = SafariReaderState(library_dir=Path(td))
            state2.current_book = BookMeta(title="BM Test", source_id="pg999")
            load_reading_state(state2)
            assert state2.current_position == 1234
            assert len(state2.bookmarks) == 1
            assert state2.bookmarks[0].name == "Mark 1"
            assert state2.bookmarks[0].position == 500

    def test_no_book_is_noop(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            state = SafariReaderState(library_dir=Path(td))
            save_reading_state(state)  # should not crash
            load_reading_state(state)  # should not crash


class TestImportLocalFile:
    def test_import_txt(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            src = Path(td) / "my-novel.txt"
            src.write_text("CHAPTER I\n\nOnce upon a time.", encoding="utf-8")
            state = SafariReaderState(library_dir=Path(td) / "lib")
            meta = import_local_file(src, state)
            assert meta.title == "My Novel"
            assert meta.source == "local"
            assert meta.file_path is not None
            assert meta.file_path.exists()
            assert len(state.library) == 1

    def test_import_html(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            src = Path(td) / "page.html"
            src.write_text(
                "<html><body><p>Hello</p><script>x</script></body></html>",
                encoding="utf-8",
            )
            state = SafariReaderState(library_dir=Path(td) / "lib")
            meta = import_local_file(src, state)
            dest_text = meta.file_path.read_text(encoding="utf-8")  # type: ignore[union-attr]
            assert "Hello" in dest_text
            assert "script" not in dest_text


class TestOpenBook:
    def test_open_sets_text_and_chapters(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            book_file = Path(td) / "book.txt"
            book_file.write_text(
                "CHAPTER I. Start\n\nHello\n\nCHAPTER II. End\n\nBye",
                encoding="utf-8",
            )
            state = SafariReaderState(library_dir=Path(td))
            book = BookMeta(title="Test", file_path=book_file)
            state.library.append(book)
            open_book(book, state)
            assert state.current_book is book
            assert len(state.current_text) > 0
            assert len(state.current_chapters) == 2

    def test_open_missing_file(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            state = SafariReaderState(library_dir=Path(td))
            book = BookMeta(title="Ghost", file_path=Path(td) / "nope.txt")
            open_book(book, state)
            assert state.current_text == ""


class TestDeleteBook:
    def test_removes_file_and_entry(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            book_file = Path(td) / "doomed.txt"
            book_file.write_text("bye", encoding="utf-8")
            state = SafariReaderState(library_dir=Path(td))
            book = BookMeta(title="Doomed", file_path=book_file)
            state.library.append(book)
            save_library(state)
            delete_book(book, state)
            assert not book_file.exists()
            assert len(state.library) == 0


class TestReaderSettings:
    def test_defaults(self) -> None:
        s = ReaderSettings()
        assert s.text_scale == 1
        assert s.line_spacing == 1
        assert s.margin_width == 1
        assert s.page_mode is True


# ── Live network tests (hit real Gutenberg API) ─────────────────


@pytest.mark.live
class TestGutenbergSearchLive:
    def test_search_returns_results(self) -> None:
        results = search_gutenberg("Pride and Prejudice")
        assert len(results) > 0
        assert any("Austen" in r.get("author", "") for r in results)

    def test_search_empty_query(self) -> None:
        results = search_gutenberg("")
        # Empty query still returns something from the API
        assert isinstance(results, list)

    def test_search_nonsense(self) -> None:
        results = search_gutenberg("xyzzy_qqq_notabook_12345")
        assert isinstance(results, list)
        # Might be empty, that's fine


@pytest.mark.live
class TestGutenbergTopLive:
    def test_top_returns_results(self) -> None:
        results = top_gutenberg()
        assert len(results) > 0
        # Top results should have titles and authors
        first = results[0]
        assert first.get("title")
        assert first.get("id")


@pytest.mark.live
class TestGutenbergDetailLive:
    def test_detail_known_book(self) -> None:
        # Pride and Prejudice is PG#1342
        detail = gutenberg_book_detail("1342")
        assert detail.get("title"), "Expected a title"
        assert "Austen" in detail.get("author", "")
        assert detail.get("txt_url"), "Expected a text download URL"

    def test_detail_nonexistent_book(self) -> None:
        detail = gutenberg_book_detail("99999999")
        # Should return empty dict or at least not crash
        assert isinstance(detail, dict)


@pytest.mark.live
class TestGutenbergDownloadLive:
    def test_download_short_book(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            # PG#11 = Alice's Adventures in Wonderland — a known, stable ID
            path = download_gutenberg_text("11", Path(td))
            assert path is not None, "Download should succeed"
            assert path.exists()
            text = path.read_text(encoding="utf-8")
            assert len(text) > 1000
            assert "Alice" in text or "ALICE" in text

    def test_download_bad_id(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            path = download_gutenberg_text("99999999", Path(td))
            # Should return None, not crash
            assert path is None


@pytest.mark.live
class TestEndToEndLive:
    """Full workflow: search → download → import → open → read."""

    def test_search_download_read(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            lib_dir = Path(td) / "library"
            state = SafariReaderState(library_dir=lib_dir)

            # Search
            results = search_gutenberg("Metamorphosis Kafka")
            assert len(results) > 0

            # Pick first result with an ID
            book_id = ""
            for r in results:
                if r.get("id"):
                    book_id = r["id"]
                    break
            assert book_id, "Should find at least one book"

            # Download
            path = download_gutenberg_text(book_id, lib_dir)
            assert path is not None

            # Add to library
            detail = gutenberg_book_detail(book_id)
            meta = add_book_to_library(detail, path, state)
            assert meta.title
            assert len(state.library) == 1

            # Open and read
            open_book(meta, state)
            assert len(state.current_text) > 100
            assert state.current_book is meta

            # Save and restore position
            state.current_position = 500
            state.bookmarks = [
                Bookmark(name="Test", position=500, chapter="", excerpt="test"),
            ]
            save_reading_state(state)

            state2 = SafariReaderState(library_dir=lib_dir)
            load_library(state2)
            assert len(state2.library) == 1
            state2.current_book = state2.library[0]
            load_reading_state(state2)
            assert state2.current_position == 500
            assert len(state2.bookmarks) == 1
