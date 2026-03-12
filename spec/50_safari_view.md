# Spec: SafariView

**A retro 8-bit Atari-style, menu-driven image viewer for modern systems**
**Target implementation language:** Python
**Target environments:** terminal first, with optional Tkinter desktop viewer
**Platforms:** Windows, macOS, Linux

## 1. Purpose

SafariView is a retro-styled image viewer that feels like an 8-bit Atari application, but runs on modern systems. It presents a menu-driven interface, keyboard-centric controls, bold old-school chrome, and mode-based image rendering that emulates three visual eras:

* **2600 mode** — very chunky pixels, tiny palette, aggressively stylized
* **800 mode** — Atari 8-bit inspired look, limited palette and visible blockiness
* **ST mode** — cleaner and more detailed, but still retro and constrained

The app has two front ends:

* **Terminal UI**

  * Primary retro shell and file browser
  * Can display images inline when the terminal supports graphics protocols
  * Falls back to colored block-art / text-mode rendering otherwise
* **Tkinter UI**

  * Same menus, themes, and behaviors
  * Uses a normal window to show the image at better fidelity
  * Not constrained by terminal cell geometry

This split is practical because terminal image support is fragmented. Some terminals support real inline raster graphics through Kitty protocol, iTerm2 inline images, or Sixel, while others require character-cell rendering. Python libraries such as `term-image` support protocol detection and fallback rendering, and Pillow is the right baseline library for decoding and transforming images. ([PyPI][1])

---

## 2. Design goals

1. **Retro first**

   * Should feel like launching a serious 1980s productivity/viewer app.
   * Menu bar, dialog boxes, shortcut hints, status line, help screens.

2. **Actually useful**

   * Open common modern image formats through third-party libraries.
   * Browse directories, preview files, zoom, pan, slideshow, metadata summary.

3. **Cross-platform**

   * Windows, macOS, Linux.
   * Must function even on terminals with no inline image support.

4. **Faithful visual modes**

   * The image is not merely resized; it is transformed into a retro display style.

5. **Same mental model in both front ends**

   * Terminal and Tkinter versions share command names, menus, and rendering modes.

6. **Safety and simplicity**

   * Read-only viewer.
   * No destructive file actions in v1.

---

## 3. Non-goals

* Not a paint program
* Not a photo editor
* Not a pixel-perfect emulator of real Atari hardware registers
* Not a game engine
* Not a file manager beyond lightweight browsing
* Not dependent on one specific terminal emulator

---

## 4. User experience summary

The user launches SafariView and sees:

* a top title bar
* a menu bar with pull-down menus
* a left pane or full-screen file list
* a preview/status area
* a bottom command bar with key hints

When opening an image, the user selects one of these views:

* **View in 2600 Mode**
* **View in 800 Mode**
* **View in ST Mode**
* **View in Native Mode** (Tkinter only, optional but useful)

In terminal mode, if inline image rendering is supported, the image appears directly in the app area. If not, the app renders a terminal-friendly approximation using Unicode blocks and color. `term-image` and related tools exist specifically to bridge those differences, and terminals differ a lot in protocol support. Kitty documents a full graphics protocol, iTerm2 documents inline images, and modern tools like `timg` explicitly fall back to block-based rendering where needed. ([PyPI][1])

---

## 5. Target architecture

## 5.1 Shared core

A common Python package should contain:

* configuration
* theme definitions
* menu definitions
* file browsing logic
* image loading
* image transformation pipeline
* retro mode quantization/downsampling rules
* keyboard command map
* metadata extraction
* slideshow logic

## 5.2 Terminal frontend

Recommended implementation approach:

* **Textual** for layout, widgets, menus, panes, keyboard handling, dialogs
* **Rich** for styled text and panels
* **term-image** or equivalent for inline image display when possible
* fallback character-cell renderer when true image display is unavailable

Textual is cross-platform and intended for sophisticated terminal apps. `term-image` supports multiple render styles and multiple terminal graphics protocols, including Kitty and iTerm2, with automatic support detection. ([Textual Documentation][2])

## 5.3 Tkinter frontend

Recommended implementation approach:

* standard `tkinter`
* Pillow + `ImageTk.PhotoImage` for rendering images in a canvas or label
* menu bar mirrored from terminal version
* resize-aware image panel

Pillow’s `ImageTk` module exists specifically to bridge PIL images into Tkinter image objects. ([Pillow (PIL Fork)][3])

---

## 6. Third-party libraries

## 6.1 Required

* **Pillow**

  * image decoding
  * resizing
  * palette conversion
  * dithering
  * metadata access
  * supports many common raster formats. ([Pillow (PIL Fork)][4])

## 6.2 Recommended

* **Textual**

  * terminal app framework
* **Rich**

  * text styling
* **term-image**

  * terminal graphics protocol support and fallback render styles. ([PyPI][1])

## 6.3 Optional

* image format helpers that Pillow can use indirectly
* watchdog for live directory refresh
* platformdirs for config paths

---

## 7. Terminal capability reality

This matters for the spec.

Modern terminals do **not** all support image display the same way:

* **Kitty** supports a full graphics protocol. ([Kovid's Software Projects][5])
* **iTerm2** supports inline images. ([iterm2.com][6])
* **Some terminals support Sixel**, and current discussions and ecosystem references indicate support is spreading, including to modern terminals. However, support is still uneven enough that it should not be the only path. ([GitHub][7])
* Tools like `timg` are explicit that they use full-resolution graphics when supported and otherwise fall back to Unicode/24-bit color rendering. ([GitHub][8])
* `term-image` also notes only partial Windows support in some configurations. ([PyPI][9])

### Spec conclusion

SafariView terminal mode must support **three rendering tiers**:

1. **Protocol image mode**

   * Kitty / iTerm2 / Sixel when available
2. **High-color cell mode**

   * Unicode half-block / full-block rendering with 24-bit color
3. **Low-fidelity text mode**

   * plain ASCII / reduced color fallback for hostile environments

This keeps the app usable everywhere.

---

## 8. Visual identity

## 8.1 Theme

The application chrome should evoke Atari-era software:

* strong borders
* inverse-video menu selection
* title bar
* blocky labels
* all-caps menu names by default
* bright accent colors on dark backgrounds
* optional phosphor-ish palettes

Suggested default palettes:

* **Blue Theme**: dark blue background, light cyan text
* **Green Screen Theme**: black background, green text
* **Amber Theme**: black background, amber text
* **ST Desktop Theme**: light background with darker UI framing

## 8.2 Typography

Terminal:

* use terminal font
* assume monospace
* avoid dependence on box-drawing behavior that fails in some environments without fallback

Tkinter:

* use a monospace font by default for chrome
* image area is not monospace-constrained

---

## 9. Main screens

## 9.1 Splash screen

Displays:

* app title
* subtitle like “RETRO IMAGE VIEWER”
* version
* short loading text
* optional rotating hint

## 9.2 Main browser screen

Contains:

* top menu bar
* current path
* file list
* filter indicator
* preview metadata pane
* status line

## 9.3 Viewer screen

Contains:

* image viewport
* current render mode
* zoom level
* palette/dither indicator
* file name
* dimensions
* help strip at bottom

## 9.4 Help screen

Contains:

* keys
* render mode descriptions
* terminal capability explanation
* supported formats

## 9.5 About screen

Contains:

* app description
* libraries used
* detected capabilities

---

## 10. Menus

Suggested top-level menus:

### FILE

* OPEN IMAGE
* OPEN FOLDER
* RECENT FILES
* RESCAN DIRECTORY
* IMAGE INFO
* EXIT

### VIEW

* VIEW 2600 MODE
* VIEW 800 MODE
* VIEW ST MODE
* VIEW NATIVE MODE
* ZOOM IN
* ZOOM OUT
* FIT TO WINDOW
* ACTUAL SIZE
* TOGGLE PIXEL GRID
* FULL SCREEN

### BROWSE

* NEXT IMAGE
* PREVIOUS IMAGE
* FIRST IMAGE
* LAST IMAGE
* GO TO FILE
* FILTER BY EXTENSION

### OPTIONS

* THEME
* DITHERING
* PALETTE VARIANT
* TERMINAL RENDERING MODE
* SLIDESHOW DELAY
* SHOW HIDDEN FILES

### HELP

* KEYBOARD HELP
* RENDER MODES
* TERMINAL SUPPORT
* ABOUT

---

## 11. Keyboard model

The app should be completely keyboard-usable.

Suggested bindings:

* `Left/Right/Up/Down` — navigate file list or pan image
* `Enter` — open selected file
* `Esc` — back/cancel/close menu
* `Tab` — switch pane
* `F1` — help
* `F2` — file browser
* `F3` — 2600 mode
* `F4` — 800 mode
* `F5` — ST mode
* `F6` — native mode
* `+` / `-` — zoom in/out
* `[` / `]` — previous/next image
* `D` — toggle dithering
* `P` — cycle palette
* `G` — toggle pixel grid
* `S` — start/stop slideshow
* `I` — image info
* `Q` — quit

Tkinter should preserve these as far as practical.

---

## 12. Supported file formats

SafariView should support whatever Pillow can decode reliably, with PNG, JPEG, GIF, BMP, TIFF, and WebP expected as common cases. Pillow supports a wide range of raster formats and determines file type from contents rather than just filename extension. ([Pillow (PIL Fork)][10])

### v1 required

* PNG
* JPEG
* GIF
* BMP

### v1 desirable

* TIFF
* WebP

### v1 out of scope

* vector graphics as first-class citizens
* video

Animated GIF support may be shown frame-by-frame later, but is optional for v1.

---

## 13. Rendering modes

## 13.1 Shared concept

Each retro mode applies a pipeline:

1. load source image
2. rotate based on metadata if desired
3. crop or fit
4. downsample to target logical resolution
5. reduce palette
6. optionally dither
7. scale to display target
8. render via terminal or Tkinter backend

The result must preserve the *aesthetic* of the chosen mode, not literal hardware behavior.

---

## 13.2 2600 mode

Intent: exaggerated, chunky, dramatic, almost toy-like.

Characteristics:

* extremely low logical resolution
* big visible pixels
* very limited color palette
* strong posterization
* optional scanline feel
* aggressive dithering allowed

Suggested default:

* downsample to something tiny such as 40–80 logical pixels wide depending on viewport
* palette restricted to a curated retro set
* optional horizontal exaggeration to mimic old display weirdness
* nearest-neighbor upscale only

This mode should look fun before it looks accurate.

---

## 13.3 800 mode

Intent: richer than 2600, still obviously 8-bit.

Characteristics:

* more detail than 2600
* palette-limited
* visible blockiness
* can include mode presets

Suggested presets:

* **800 GR.7-ish**
* **800 GR.8-ish monochrome**
* **800 colorful mixed mode look**

The app does not need true hardware mode simulation, but should offer a few recognizable “personalities.”

---

## 13.4 ST mode

Intent: cleaner, sharper, more late-80s desktop.

Characteristics:

* higher logical resolution
* less aggressive chunking
* reduced but broader palette
* more faithful image composition
* optional low/medium/high style presets

This is the best retro mode for actually viewing photos or illustrations in a useful way.

---

## 13.5 Native mode

Tkinter only, and optional in terminal where supported.

Intent:

* display the image without retro degradation
* useful as a comparison mode

---

## 14. Rendering backends

## 14.1 Terminal protocol image backend

Used when terminal capability detection succeeds.

Supports:

* inline raster image output in supported terminals
* fit-to-pane scaling
* better fidelity than text-cell mode

Priority order:

1. kitty graphics protocol
2. iTerm2 inline images
3. sixel
4. fallback renderer

This ordering may be configurable.

## 14.2 Terminal cell renderer

Used everywhere else.

Techniques:

* Unicode half blocks
* full blocks
* braille or shaded blocks optionally
* 24-bit color where available
* 256-color fallback
* 16-color emergency fallback

This renderer must be deterministic and tested.

## 14.3 Tkinter canvas renderer

Displays the transformed PIL image in a resizable window or pane.

Capabilities:

* smooth resize
* optional pixel-grid overlay
* zoom and pan
* better slideshow support

---

## 15. Terminal capability detection

On startup, SafariView should detect:

* OS
* terminal emulator hints from environment variables
* color depth
* Unicode capability assumptions
* likely support for:

  * kitty graphics
  * iTerm2 inline images
  * sixel

The detection result should be viewable in **Help → Terminal Support**.

The user must be allowed to override auto-detection.

Example override options:

* FORCE BLOCK MODE
* FORCE SIXEL
* FORCE KITTY
* FORCE ASCII
* AUTO

Because support is inconsistent, manual override is essential. `term-image` and similar tools already treat capability detection as a core feature. ([PyPI][1])

---

## 16. File browser behavior

## 16.1 Directory listing

Show:

* filename
* type marker
* size or dimensions when cheaply available
* sort indicator

## 16.2 Sorting

Support:

* name
* date
* size
* type

## 16.3 Filtering

Support:

* all files
* known image files only
* extension filter

## 16.4 Preview behavior

Selecting a file without opening it should show:

* filename
* dimensions if available
* file size
* format
* modified date

---

## 17. Viewer behavior

## 17.1 Open image

When an image is opened:

* render in the current mode
* fit to current viewport by default
* update title/status bars

## 17.2 Navigation

When browsing within a folder:

* next/previous skips non-image files unless configured otherwise
* wraparound optional

## 17.3 Zoom

Support:

* fit
* 1x
* 2x
* 4x
* custom step zoom

For retro modes, zoom should preserve chunky nearest-neighbor scaling.

## 17.4 Pan

If zoomed beyond fit:

* arrow keys pan
* mouse drag in Tkinter optional

## 17.5 Slideshow

Support:

* start slideshow from current image
* configurable delay
* pause/resume
* mode locked or per-image inherited

---

## 18. Dithering and palette rules

Users should be able to choose:

* no dithering
* ordered dithering
* Floyd–Steinberg or equivalent error diffusion
* automatic per mode

Users should also be able to select palette variants:

* warm
* cool
* grayscale
* “authentic-ish”
* high contrast

The spec should allow palettes to be data-driven so new retro looks can be added without rewriting the pipeline.

---

## 19. Metadata

SafariView should expose light metadata:

* format
* width/height
* mode
* frame count if animated
* file size
* modified timestamp

Optional future metadata:

* EXIF summary
* camera info

---

## 20. Configuration

Config file should include:

* default frontend
* default render mode
* theme
* slideshow delay
* last-opened folder
* dithering default
* palette default
* terminal backend override
* keybinding overrides

Use platform-appropriate config directories.

---

## 21. Error handling

Errors should appear in retro dialog boxes.

Cases:

* unsupported file
* corrupt image
* permission denied
* protocol rendering failure
* terminal too small
* missing optional dependency

Behavior:

* never crash to raw traceback in normal use
* provide concise message
* offer fallback when possible

Example:
“INLINE IMAGE MODE FAILED. FALLING BACK TO BLOCK RENDERER.”

---

## 22. Accessibility and usability

Even though the app is retro-themed, it should still be practical.

Include:

* high contrast themes
* configurable key repeat sensitivity where relevant
* option to reduce flashing
* option to disable faux CRT effects
* option to enlarge UI chrome in Tkinter

---

## 23. Proposed package layout

```text
safariview/
  __init__.py
  app.py
  config.py
  models.py
  themes.py
  keymap.py
  browser.py
  metadata.py
  capabilities.py
  render/
    __init__.py
    pipeline.py
    palettes.py
    dither.py
    mode_2600.py
    mode_800.py
    mode_st.py
    terminal_backend.py
    terminal_blocks.py
    tkinter_backend.py
  ui_terminal/
    __init__.py
    textual_app.py
    screens.py
    dialogs.py
    menus.py
  ui_tk/
    __init__.py
    tk_app.py
    widgets.py
    menus.py
  assets/
    palettes/
    help/
  tests/
```

---

## 24. Frontend parity requirements

The two front ends must share:

* same menu names
* same mode names
* same config
* same render pipeline
* same directory and image navigation rules

They may differ in:

* actual image fidelity
* mouse support
* window resizing behavior
* full-screen behavior

---

## 25. Suggested implementation phases

## Phase 1: core prototype

* load images with Pillow
* implement 2600/800/ST transforms
* Tkinter proof of concept
* save screenshots for comparison

## Phase 2: terminal prototype

* Textual shell
* file browser
* block-render fallback
* status/help screens

## Phase 3: protocol graphics

* add `term-image`
* capability detection
* backend selection and override

## Phase 4: polish

* menus
* dialogs
* themes
* slideshow
* metadata panel

## Phase 5: packaging

* cross-platform install
* optional extras for terminal image support

---

## 26. Acceptance criteria

SafariView v1 is acceptable if:

1. It runs on Windows, macOS, and Linux in at least one supported configuration.
2. It can open common image formats via Pillow. ([Pillow (PIL Fork)][10])
3. It has both terminal and Tkinter front ends.
4. It offers 2600, 800, and ST visual modes.
5. The terminal version works without inline graphics by using a cell renderer.
6. The terminal version uses richer inline image protocols when available. ([PyPI][1])
7. The UI is menu driven and keyboard navigable.
8. The look and feel is recognizably retro.

---

## 27. Recommendation

For a real implementation, the safest stack is:

* **Pillow** for image I/O and processing
* **Textual** for terminal UI
* **term-image** for terminal protocol display and fallback detection
* **Tkinter + ImageTk** for desktop viewer

That gives you the best balance of retro UI control, cross-platform behavior, and realistic terminal-image support today. ([PyPI][1])

The practical answer to your concern is: **modern terminals do have some flexibility for images, but not enough to treat inline graphics as universal.** So the spec should treat true terminal image display as an enhancement, not the foundation. The foundation should be a robust retro TUI plus a guaranteed-good Tkinter viewer.

[1]: https://pypi.org/project/term-image/?utm_source=chatgpt.com "term-image"
[2]: https://textual.textualize.io/?utm_source=chatgpt.com "Textual"
[3]: https://pillow.readthedocs.io/en/latest/reference/ImageTk.html?utm_source=chatgpt.com "ImageTk module - Pillow (PIL Fork) 12.2.0.dev0 documentation"
[4]: https://pillow.readthedocs.io/?utm_source=chatgpt.com "Pillow (PIL Fork) 12.1.1 documentation"
[5]: https://sw.kovidgoyal.net/kitty/graphics-protocol/?utm_source=chatgpt.com "Terminal graphics protocol - kitty"
[6]: https://iterm2.com/documentation-images.html?utm_source=chatgpt.com "Inline Images Protocol"
[7]: https://github.com/Ylianst/MeshCentral/issues/7591?utm_source=chatgpt.com "Add xterm-addon-image support for inline ..."
[8]: https://github.com/hzeller/timg?utm_source=chatgpt.com "GitHub - hzeller/timg: A terminal image and video viewer."
[9]: https://pypi.org/project/term-image/0.3.0/?utm_source=chatgpt.com "term-image"
[10]: https://pillow.readthedocs.io/en/stable/handbook/tutorial.html?utm_source=chatgpt.com "Tutorial - Pillow (PIL Fork) 12.1.1 documentation"
