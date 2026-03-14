"""Public library interface for Safari Writer."""

# pylint: disable=undefined-all-variable

from __future__ import annotations

from importlib import import_module

__all__ = [
    "AppState",
    "DEMO_DOCUMENT_RESOURCE",
    "DEMO_MAILMERGE_RESOURCE",
    "FileProfile",
    "HighlightProfile",
    "DEFAULT_FIELDS",
    "FieldDef",
    "GlobalFormat",
    "LOCALE",
    "LOCALE_LANGUAGE",
    "LOCALE_REGION",
    "MAX_FIELD_DATA_LEN",
    "MAX_FIELD_NAME_LEN",
    "MAX_FIELDS",
    "MAX_RECORDS",
    "MailMergeDB",
    "StorageMode",
    "SafariWriterApp",
    "StartupRequest",
    "apply_mail_merge_to_buffer",
    "available_languages",
    "build_parser",
    "build_startup_request",
    "check_word",
    "count_ansi_pages",
    "decode_sfw",
    "dict_lookup",
    "encode_sfw",
    "export_pdf",
    "export_markdown",
    "export_postscript",
    "extract_ansi_page",
    "extract_sfw_metadata",
    "extract_words",
    "format_datetime",
    "get_locale",
    "get_translation",
    "has_controls",
    "inject_sfw_metadata",
    "inspect_mail_merge_db",
    "is_sfw",
    "load_demo_document_buffer",
    "load_demo_mail_merge_db",
    "load_document_buffer",
    "load_document_state",
    "load_mail_merge_db",
    "load_personal_dictionary",
    "load_sfw_language",
    "make_checker",
    "parse_args",
    "render_ansi_preview",
    "resolve_file_profile",
    "run_cli",
    "save_mail_merge_db",
    "serialize_document_buffer",
    "strip_controls",
    "suggest_words",
    "validate_mail_merge_data",
]

_EXPORTS: dict[str, tuple[str, str]] = {
    "count_ansi_pages": ("safari_writer.ansi_preview", "count_ansi_pages"),
    "extract_ansi_page": ("safari_writer.ansi_preview", "extract_ansi_page"),
    "render_ansi_preview": ("safari_writer.ansi_preview", "render_ansi_preview"),
    "SafariWriterApp": ("safari_writer.app", "SafariWriterApp"),
    "StartupRequest": ("safari_writer.cli_types", "StartupRequest"),
    "DEMO_DOCUMENT_RESOURCE": (
        "safari_writer.document_io",
        "DEMO_DOCUMENT_RESOURCE",
    ),
    "DEMO_MAILMERGE_RESOURCE": (
        "safari_writer.document_io",
        "DEMO_MAILMERGE_RESOURCE",
    ),
    "load_demo_document_buffer": (
        "safari_writer.document_io",
        "load_demo_document_buffer",
    ),
    "load_demo_mail_merge_db": (
        "safari_writer.document_io",
        "load_demo_mail_merge_db",
    ),
    "load_document_buffer": ("safari_writer.document_io", "load_document_buffer"),
    "load_document_state": ("safari_writer.document_io", "load_document_state"),
    "load_sfw_language": ("safari_writer.document_io", "load_sfw_language"),
    "serialize_document_buffer": (
        "safari_writer.document_io",
        "serialize_document_buffer",
    ),
    "export_markdown": ("safari_writer.export_md", "export_markdown"),
    "export_pdf": ("safari_writer.export_pdf", "export_pdf"),
    "export_postscript": ("safari_writer.export_ps", "export_postscript"),
    "FileProfile": ("safari_writer.file_types", "FileProfile"),
    "HighlightProfile": ("safari_writer.file_types", "HighlightProfile"),
    "StorageMode": ("safari_writer.file_types", "StorageMode"),
    "resolve_file_profile": ("safari_writer.file_types", "resolve_file_profile"),
    "decode_sfw": ("safari_writer.format_codec", "decode_sfw"),
    "encode_sfw": ("safari_writer.format_codec", "encode_sfw"),
    "extract_sfw_metadata": ("safari_writer.format_codec", "extract_sfw_metadata"),
    "has_controls": ("safari_writer.format_codec", "has_controls"),
    "inject_sfw_metadata": ("safari_writer.format_codec", "inject_sfw_metadata"),
    "is_sfw": ("safari_writer.format_codec", "is_sfw"),
    "strip_controls": ("safari_writer.format_codec", "strip_controls"),
    "LOCALE_LANGUAGE": ("safari_writer.locale_info", "LANGUAGE"),
    "LOCALE": ("safari_writer.locale_info", "LOCALE"),
    "LOCALE_REGION": ("safari_writer.locale_info", "REGION"),
    "available_languages": ("safari_writer.locale_info", "available_languages"),
    "format_datetime": ("safari_writer.locale_info", "format_datetime"),
    "get_locale": ("safari_writer.locale_info", "get_locale"),
    "get_translation": ("safari_writer.locale_info", "get_translation"),
    "DEFAULT_FIELDS": ("safari_writer.mail_merge_db", "DEFAULT_FIELDS"),
    "MAX_FIELD_DATA_LEN": ("safari_writer.mail_merge_db", "MAX_FIELD_DATA_LEN"),
    "MAX_FIELD_NAME_LEN": ("safari_writer.mail_merge_db", "MAX_FIELD_NAME_LEN"),
    "MAX_FIELDS": ("safari_writer.mail_merge_db", "MAX_FIELDS"),
    "MAX_RECORDS": ("safari_writer.mail_merge_db", "MAX_RECORDS"),
    "FieldDef": ("safari_writer.mail_merge_db", "FieldDef"),
    "MailMergeDB": ("safari_writer.mail_merge_db", "MailMergeDB"),
    "apply_mail_merge_to_buffer": (
        "safari_writer.mail_merge_db",
        "apply_mail_merge_to_buffer",
    ),
    "inspect_mail_merge_db": ("safari_writer.mail_merge_db", "inspect_mail_merge_db"),
    "load_mail_merge_db": ("safari_writer.mail_merge_db", "load_mail_merge_db"),
    "save_mail_merge_db": ("safari_writer.mail_merge_db", "save_mail_merge_db"),
    "validate_mail_merge_data": (
        "safari_writer.mail_merge_db",
        "validate_mail_merge_data",
    ),
    "build_parser": ("safari_writer.main", "build_parser"),
    "build_startup_request": ("safari_writer.main", "build_startup_request"),
    "run_cli": ("safari_writer.main", "main"),
    "parse_args": ("safari_writer.main", "parse_args"),
    "check_word": ("safari_writer.proofing", "check_word"),
    "dict_lookup": ("safari_writer.proofing", "dict_lookup"),
    "extract_words": ("safari_writer.proofing", "extract_words"),
    "load_personal_dictionary": (
        "safari_writer.proofing",
        "load_personal_dictionary",
    ),
    "make_checker": ("safari_writer.proofing", "make_checker"),
    "suggest_words": ("safari_writer.proofing", "suggest_words"),
    "AppState": ("safari_writer.state", "AppState"),
    "GlobalFormat": ("safari_writer.state", "GlobalFormat"),
}


def __getattr__(name: str) -> object:
    try:
        module_name, attr_name = _EXPORTS[name]
    except KeyError as exc:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from exc
    value = getattr(import_module(module_name), attr_name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
