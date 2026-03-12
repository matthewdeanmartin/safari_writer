# SafariView

A retro 8-bit Atari-style image viewer for modern terminals and desktops.

## Features

* **Retro Rendering Modes**:
    * **2600**: Extremely chunky pixels, limited palette.
    * **800**: Classic 8-bit look.
    * **ST**: Cleaner, higher resolution retro look.
* **Pixel Grid**: Optional overlay to enhance the chunky feel.
* **Two Frontends**:
    * **Terminal (Textual)**: Integrated file browser and Unicode block-art rendering.
    * **Desktop (Tkinter)**: High-fidelity windowed viewer.

## Installation

```bash
pip install .
```

## Usage

### Terminal UI
```bash
safari-view [path]
```

### Desktop UI
```bash
safari-view-tk [path]
```

## Key Bindings

* `F2`: Toggle File Browser (Terminal)
* `F3`: 2600 Mode
* `F4`: 800 Mode
* `F5`: ST Mode
* `F6`: Native Mode
* `D`: Toggle Dithering
* `G`: Toggle Pixel Grid
* `Q`: Quit
