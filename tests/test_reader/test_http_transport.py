"""Exercise Reader downloads through the actual HTTPX2 socket transport."""

from __future__ import annotations

import json
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

import pytest

from safari_fed import services as feed_services
from safari_reader import services


@pytest.fixture
def book_server(monkeypatch: pytest.MonkeyPatch) -> Iterator[str]:
    """Serve metadata, a redirect, and UTF-8 content without external services."""

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            if self.path == "/books/1":
                body = json.dumps(
                    {
                        "id": 1,
                        "title": "Test Book",
                        "formats": {
                            "text/plain; charset=utf-8": f"{base_url}/redirect"
                        },
                    }
                ).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
            elif self.path == "/redirect":
                body = b""
                self.send_response(302)
                self.send_header("Location", "/text")
            elif self.path == "/text":
                body = "A caf\u00e9 in a book.".encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
            else:
                body = b"missing"
                self.send_response(404)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format_string: str, *args: object) -> None:
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    base_url = f"http://127.0.0.1:{server.server_port}"
    monkeypatch.setenv("NO_PROXY", "127.0.0.1")
    worker = Thread(target=server.serve_forever, daemon=True)
    worker.start()
    try:
        yield base_url
    finally:
        server.shutdown()
        worker.join(timeout=5)
        server.server_close()


def test_reader_download_follows_redirect_and_preserves_utf8(
    book_server: str, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(services, "GUTENBERG_API", f"{book_server}/books")
    downloaded = services.download_gutenberg_text("1", tmp_path / "library")
    assert downloaded is not None
    assert downloaded.name == "pg1_test_book.txt"
    assert downloaded.read_text(encoding="utf-8") == "A caf\u00e9 in a book."


def test_reader_handles_http_error(
    book_server: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(services, "GUTENBERG_API", f"{book_server}/missing")
    assert services.search_gutenberg("example") == []


def test_feed_transport_follows_redirect(book_server: str) -> None:
    response = feed_services._default_get(f"{book_server}/redirect")
    assert response.status_code == 200
    assert response.text == "A caf\u00e9 in a book."
