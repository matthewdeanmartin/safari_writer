# Global Format v2 Notes

This document records implementation behavior that extends `spec/03_global_format.md`.

## A new `K` language field exists

The Global Format screen now includes a `K` row for per-document spell-check language selection. This is not part of the original Global Format spec, but it is implemented and wired through the document model.

Current behavior:

- `K` edits `AppState.doc_language`
- the field displays the effective document language or `(auto)`
- `.sfw` files can persist the choice through `%%lang:` metadata

Implementation references:

- `safari_writer/screens/global_format.py`
- `safari_writer/state.py`
- `safari_writer/document_io.py`
- `safari_writer/format_codec.py`

## The screen now carries i18n responsibilities

In practice, Global Format is no longer just layout/pagination. It also acts as the document-level language control surface for proofing. Future specs should treat that as part of the screen contract.
