# Safari View

Safari View is a retro image viewer and renderer. It can browse folders in a Textual UI, open a single image directly, launch a Tk frontend, or batch-render files through the command line.

## Starting Safari View

```bash
safari-view
safari-view tui .
safari-view browse images --select images\frog.png
safari-view open images\frog.png --mode st --no-dithering
safari-view tk --image images\frog.png --mode native
safari-view render images\frog.png --mode 2600 --width 160 --height 192 -o out\frog-2600.png
safari-view modes
```

If you run `safari-view` with no subcommand, it falls back to the Textual viewer and opens the current directory.

## Textual Viewer Controls

- **F2** — Toggle the file browser pane.
- **F3 / F4 / F5 / F6** — Switch to 2600, 800, ST, or Native render mode.
- **D** — Toggle dithering.
- **G** — Toggle the pixel grid.
- **Enter** — Open the selected image.
- **Esc** — Return to the previous screen.
- **Q** — Quit.

## Render Modes

- **2600** — Ultra-low-resolution retro rendering.
- **800** — Atari 8-bit inspired rendering.
- **ST** — Atari ST inspired rendering.
- **Native** — Native-size rendering with the same viewer pipeline.

## CLI Workflows

- `safari-view tui PATH` — Launch the Textual frontend explicitly.
- `safari-view browse PATH` — Start in a directory-focused browser session.
- `safari-view open IMAGE` — Open one image directly in the Textual frontend.
- `safari-view tk --image IMAGE` — Use the Tk frontend instead of Textual.
- `safari-view render IMAGE -o OUTPUT.png` — Render an image without opening the UI.
- `safari-view modes` — Print the supported render modes.

## Startup options

The Textual and Tk frontends share a few useful startup flags:

- `--mode 2600|800|st|native` — Pick the initial render mode.
- `--dithering` / `--no-dithering` — Turn dithering on or off.
- `--pixel-grid` / `--no-pixel-grid` — Toggle the retro pixel grid overlay.
- `--browser show|hide` — Control whether the file browser starts visible in the Textual UI.
- `--focus browser|viewer` — Choose the startup focus in the Textual UI.
- `--select PATH` — Preselect a file or folder in the browser.
