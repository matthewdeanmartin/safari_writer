# Safari DOS TODO

These items are described in `spec/09_safari_dos.md` but are still missing or only partially implemented.

## 1. In-app garbage browsing and restore

Spec intent:

- browse garbage-managed items when applicable
- restore to original location
- restore to alternate location if needed

Current implementation:

- deletion goes to OS trash via `send2trash`
- `list_garbage()` always returns an empty list
- `restore_from_garbage()` is not supported
- the Garbage screen tells the user to use the system file manager to restore items

Implementation references:

- `safari_dos/services.py`
- `safari_dos/screens.py`

## 2. Conflict-resolution choices for copy/move are not implemented

Spec intent:

- offer explicit conflict handling such as skip, rename, or replace-with-confirmation

Current implementation:

- copy and move raise `FileExistsError` when a destination already exists
- there is no in-app conflict-resolution workflow for bulk operations

Implementation references:

- `safari_dos/services.py`
- `safari_dos/screens.py`

## 3. Progress and end-report screens are still missing

Spec intent:

- longer operations should show progress
- state-changing operations should end with plain-language summaries

Current implementation:

- operations run directly and report via short status messages
- there is no dedicated progress screen or completion-report workflow

Implementation references:

- `safari_dos/screens.py`
- `safari_dos/services.py`

## 4. Search is still a local filter, not the fuller DOS search model

Spec intent:

- support a search workflow that can show result lists and optionally search beyond the current visible list

Current implementation:

- `/` opens a name filter for the current directory listing
- there is no separate recursive results workflow

Implementation references:

- `safari_dos/screens.py`
- `safari_dos/state.py`
