"""Tests for safari_writer.format_codec — .sfw encode/decode and control stripping."""

import pytest

from safari_writer.format_codec import (
    decode_sfw,
    encode_sfw,
    has_controls,
    is_sfw,
    strip_controls,
)


class TestIsSfw:
    def test_sfw_extension(self):
        assert is_sfw("doc.sfw") is True

    def test_sfw_uppercase(self):
        assert is_sfw("doc.SFW") is True

    def test_txt_extension(self):
        assert is_sfw("doc.txt") is False

    def test_no_extension(self):
        assert is_sfw("readme") is False

    def test_sfw_in_path(self):
        assert is_sfw("/some/path/letter.sfw") is True


class TestEncodeSfw:
    def test_plain_text_unchanged(self):
        buf = ["Hello world", "Second line"]
        result = encode_sfw(buf)
        assert result == "Hello world\nSecond line"

    def test_bold_encoded(self):
        buf = ["\x01Hello\x01"]
        result = encode_sfw(buf)
        assert result == "\\BHello\\B"

    def test_underline_encoded(self):
        buf = ["\x02text\x02"]
        result = encode_sfw(buf)
        assert result == "\\Utext\\U"

    def test_all_markers_encode(self):
        buf = ["\x01\x02\x03\x04\x05\x06\x07\x10\x11\x12\x13\x14\x15\x16\x17"]
        result = encode_sfw(buf)
        assert result == "\\B\\U\\C\\R\\G\\^\\v\\P\\@\\H:\\F:\\S\\E\\>\\_"

    def test_backslash_escaped(self):
        buf = ["path\\to\\file"]
        result = encode_sfw(buf)
        assert result == "path\\\\to\\\\file"

    def test_multiline(self):
        buf = ["\x01bold\x01", "plain", "\x02under\x02"]
        result = encode_sfw(buf)
        assert result == "\\Bbold\\B\nplain\n\\Uunder\\U"

    def test_header_marker(self):
        buf = ["\x12My Header"]
        result = encode_sfw(buf)
        assert result == "\\H:My Header"

    def test_footer_marker(self):
        buf = ["\x13My Footer"]
        result = encode_sfw(buf)
        assert result == "\\F:My Footer"

    def test_empty_buffer(self):
        buf = [""]
        result = encode_sfw(buf)
        assert result == ""


class TestDecodeSfw:
    def test_plain_text_unchanged(self):
        result = decode_sfw("Hello world\nLine two")
        assert result == ["Hello world", "Line two"]

    def test_bold_decoded(self):
        result = decode_sfw("\\BHello\\B")
        assert result == ["\x01Hello\x01"]

    def test_all_markers_decode(self):
        encoded = "\\B\\U\\C\\R\\G\\^\\v\\P\\@\\H:\\F:\\S\\E\\>\\_"
        result = decode_sfw(encoded)
        assert result == [
            "\x01\x02\x03\x04\x05\x06\x07\x10\x11\x12\x13\x14\x15\x16\x17"
        ]

    def test_backslash_decoded(self):
        result = decode_sfw("path\\\\to\\\\file")
        assert result == ["path\\to\\file"]

    def test_unrecognised_escape_preserved(self):
        result = decode_sfw("\\Xhello")
        assert result == ["\\Xhello"]

    def test_header_decoded(self):
        result = decode_sfw("\\H:My Header")
        assert result == ["\x12My Header"]

    def test_footer_decoded(self):
        result = decode_sfw("\\F:My Footer")
        assert result == ["\x13My Footer"]

    def test_empty_text(self):
        result = decode_sfw("")
        assert result == [""]

    def test_trailing_backslash(self):
        result = decode_sfw("hello\\")
        assert result == ["hello\\"]


class TestRoundTrip:
    """Encoding then decoding should produce the original buffer."""

    def test_plain_text(self):
        buf = ["Hello", "World"]
        assert decode_sfw(encode_sfw(buf)) == buf

    def test_with_formatting(self):
        buf = ["\x01bold\x01 and \x02under\x02", "\x03centered line"]
        assert decode_sfw(encode_sfw(buf)) == buf

    def test_with_backslashes(self):
        buf = ["C:\\Users\\test\\file.txt"]
        assert decode_sfw(encode_sfw(buf)) == buf

    def test_mixed(self):
        buf = [
            "\x12Document Title",
            "\x01Hello\x01 \\world",
            "",
            "\x15",
            "\x16nextfile.sfw",
        ]
        assert decode_sfw(encode_sfw(buf)) == buf

    def test_all_controls(self):
        buf = ["\x01\x02\x03\x04\x05\x06\x07\x10\x11\x12\x13\x14\x15\x16\x17"]
        assert decode_sfw(encode_sfw(buf)) == buf


class TestStripControls:
    def test_removes_bold(self):
        buf = ["\x01Hello\x01 world"]
        result = strip_controls(buf)
        assert result == ["Hello world"]

    def test_removes_all_controls(self):
        buf = ["\x01\x02\x03text\x04\x05"]
        result = strip_controls(buf)
        assert result == ["text"]

    def test_preserves_plain_text(self):
        buf = ["Hello world", "No controls here"]
        result = strip_controls(buf)
        assert result == buf

    def test_empty_line(self):
        buf = [""]
        result = strip_controls(buf)
        assert result == [""]

    def test_line_of_only_controls(self):
        buf = ["\x01\x02\x03"]
        result = strip_controls(buf)
        assert result == [""]


class TestHasControls:
    def test_no_controls(self):
        buf = ["Hello", "World"]
        assert has_controls(buf) is False

    def test_with_bold(self):
        buf = ["\x01bold\x01"]
        assert has_controls(buf) is True

    def test_empty_buffer(self):
        buf = [""]
        assert has_controls(buf) is False

    def test_control_on_second_line(self):
        buf = ["plain", "\x02text\x02"]
        assert has_controls(buf) is True
