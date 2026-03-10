# Safari DOS Preview and Archives TODO

These items are described in `spec/13_safari_dos_preview_and_archives.md` but are still missing or only partially implemented.

## 1. Image preview is not implemented

Spec intent:

- preview PNG/JPG/BMP/GIF content
- optionally use Pillow for scaled preview or a metadata/binary fallback

Current implementation:

- preview is text/code-oriented
- `get_preview_syntax()` uses Rich/Pygments-style text rendering
- there is no image-specific preview path

Implementation references:

- `safari_dos/services.py`
- `safari_dos/screens.py`

## 2. Preview loading is not asynchronous

Spec intent:

- preview updates should avoid navigation stutter
- loading should be asynchronous or otherwise non-blocking

Current implementation:

- preview content is loaded directly during selection updates
- there is no async worker/thread/task boundary around preview generation

Implementation references:

- `safari_dos/screens.py`
- `safari_dos/services.py`

## 3. Archive progress and preflight checks are minimal

Spec intent:

- show archive/extract progress
- check practical preconditions such as available space

Current implementation:

- ZIP and unzip use straightforward direct calls
- corrupt archives are handled through `zipfile` validation
- there is no dedicated progress UI or disk-space preflight

Implementation references:

- `safari_dos/services.py`
- `safari_dos/screens.py`
