# Safari DOS v2 Notes

This document records Safari DOS behavior that exists in the implementation but is not fully captured by `spec/09_safari_dos.md`, or has evolved into a different but intentional shape.

## Garbage is implemented as OS-trash passthrough

The spec allows operating-system trash integration where possible. The current implementation leans fully into that path:

- send items to OS trash / recycle bin
- show an explanatory in-app Garbage screen
- leave browsing/restoration to the system file manager

This is a meaningful product-shape decision and should be documented explicitly rather than implied.

Implementation references:

- `safari_dos/services.py`
- `safari_dos/screens.py`

## Favorites and recents are shared workflow features

The implementation includes:

- favorites
- recent locations
- recent documents shared with Writer

This goes beyond the base DOS spec's simpler location model and reflects a stronger writer-project workflow.

Implementation references:

- `safari_dos/services.py`
- `safari_dos/screens.py`
- `safari_dos/state.py`

## Multi-select, filter, sort, protect, and preview state are first-class state

The implementation has an explicit state model for:

- multi-select
- current filter text
- sort field and direction
- preview visibility / fullscreen state

That stateful browser model is more concrete than the prose spec and should be reflected in future revisions.

Implementation references:

- `safari_dos/state.py`
- `safari_dos/screens.py`
