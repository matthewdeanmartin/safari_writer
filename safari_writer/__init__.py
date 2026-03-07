"""Public library interface for Safari Writer."""

from safari_writer.ansi_preview import count_ansi_pages, extract_ansi_page, render_ansi_preview
from safari_writer.app import SafariWriterApp
from safari_writer.cli_types import StartupRequest
from safari_writer.document_io import (
    load_document_buffer,
    load_document_state,
    serialize_document_buffer,
)
from safari_writer.export_md import export_markdown
from safari_writer.export_ps import export_postscript
from safari_writer.format_codec import decode_sfw, encode_sfw, has_controls, is_sfw, strip_controls
from safari_writer.mail_merge_db import (
    DEFAULT_FIELDS,
    MAX_FIELD_DATA_LEN,
    MAX_FIELD_NAME_LEN,
    MAX_FIELDS,
    MAX_RECORDS,
    FieldDef,
    MailMergeDB,
    apply_mail_merge_to_buffer,
    inspect_mail_merge_db,
    load_mail_merge_db,
    save_mail_merge_db,
    validate_mail_merge_data,
)
from safari_writer.main import build_parser, build_startup_request, main as run_cli, parse_args
from safari_writer.proofing import (
    check_word,
    dict_lookup,
    extract_words,
    load_personal_dictionary,
    make_checker,
    suggest_words,
)
from safari_writer.state import AppState, GlobalFormat

__all__ = [
    "AppState",
    "DEFAULT_FIELDS",
    "FieldDef",
    "GlobalFormat",
    "MAX_FIELD_DATA_LEN",
    "MAX_FIELD_NAME_LEN",
    "MAX_FIELDS",
    "MAX_RECORDS",
    "MailMergeDB",
    "SafariWriterApp",
    "StartupRequest",
    "apply_mail_merge_to_buffer",
    "build_parser",
    "build_startup_request",
    "check_word",
    "count_ansi_pages",
    "decode_sfw",
    "dict_lookup",
    "encode_sfw",
    "export_markdown",
    "export_postscript",
    "extract_ansi_page",
    "extract_words",
    "has_controls",
    "inspect_mail_merge_db",
    "is_sfw",
    "load_document_buffer",
    "load_document_state",
    "load_mail_merge_db",
    "load_personal_dictionary",
    "make_checker",
    "parse_args",
    "render_ansi_preview",
    "run_cli",
    "save_mail_merge_db",
    "serialize_document_buffer",
    "strip_controls",
    "suggest_words",
    "validate_mail_merge_data",
]
