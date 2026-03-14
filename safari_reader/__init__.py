"""Public interface for Safari Reader."""

from safari_reader.app import SafariReaderApp
from safari_reader.main import build_parser, main, parse_args
from safari_reader.services import (
    add_book_to_library,
    delete_book,
    download_gutenberg_text,
    format_book_text,
    gutenberg_book_detail,
    import_local_file,
    load_library,
    load_reading_state,
    parse_chapters,
    save_library,
    save_reading_state,
    search_gutenberg,
    strip_html_tags,
    top_gutenberg,
)
from safari_reader.state import (
    Bookmark,
    BookMeta,
    ReaderSettings,
    SafariReaderExitRequest,
    SafariReaderState,
)

__all__ = [
    "BookMeta",
    "Bookmark",
    "ReaderSettings",
    "SafariReaderApp",
    "SafariReaderExitRequest",
    "SafariReaderState",
    "add_book_to_library",
    "build_parser",
    "delete_book",
    "download_gutenberg_text",
    "format_book_text",
    "gutenberg_book_detail",
    "import_local_file",
    "load_library",
    "load_reading_state",
    "main",
    "parse_args",
    "parse_chapters",
    "save_library",
    "save_reading_state",
    "search_gutenberg",
    "strip_html_tags",
    "top_gutenberg",
]
