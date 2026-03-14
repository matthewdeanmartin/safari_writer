authors:

- name: Matthew Dean Martin
  type: human
  roles:
  - project author
  - maintainer
- name: Copilot
  type: ai
  model: GPT-5.4
  roles:
  - implemented Python type annotations
  - introduced mypy configuration and Makefile target
  - added shared typing helpers and typed package metadata
  - integrated the startup splash screen and CLI --no-splash support
- name: Gemini CLI
  type: ai
  model: Gemini 2.0 Flash
  roles:
  - fixed Safari DOS integration crash and implemented cross-app quit protocol
  - overhauled Mail Merge module with direct record entry, save-early support, and subset filtering
  - implemented full Search & Replace with wildcard support and wrapping search
  - corrected Safari Writer layout with top-docked tabs and bottom-docked command stack
- name: Claude Code
  type: ai
  model: Claude Opus 4.6
  roles:
  - fixed editor viewport scrolling bug — cursor now stays visible when typing or navigating beyond the screen

______________________________________________________________________

# AUTHORS

- Matthew Dean Martin (Human)
- Copilot (AI)
- Gemini CLI (AI) - *Helping ship Safari Writer on time.*
- Claude Code (AI) - *Fixed the scroll bug no one else could.*
