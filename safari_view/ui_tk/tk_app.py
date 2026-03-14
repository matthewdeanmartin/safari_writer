"""
SafariView Tkinter Desktop UI.
Provides a higher-fidelity windowed image viewer.
"""

from __future__ import annotations

import sys
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox

from PIL import ImageTk

from safari_view.render import RenderContext, RenderMode, create_pipeline
from safari_view.state import SafariViewState


class SafariViewTkApp:
    """Tkinter application for SafariView."""

    def __init__(self, state: SafariViewState | None = None) -> None:
        self.state = state or SafariViewState()
        self.pipeline = create_pipeline()

        self.root = tk.Tk()
        self.root.title("SafariView - Retro Image Viewer")
        self.root.geometry("800x600")
        self.root.configure(bg="#000033")

        self._setup_menu()
        self._setup_ui()

        self.tk_image: ImageTk.PhotoImage | None = None
        self.current_path = self.state.current_path

        if self.state.current_image_path:
            self._load_and_render_image(self.state.current_image_path)

    def _setup_menu(self) -> None:
        menubar = tk.Menu(self.root)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Open Image...", command=self._on_open_file)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="FILE", menu=file_menu)

        view_menu = tk.Menu(menubar, tearoff=0)
        view_menu.add_command(
            label="2600 Mode (F3)", command=lambda: self._set_mode(RenderMode.MODE_2600)
        )
        view_menu.add_command(
            label="800 Mode (F4)", command=lambda: self._set_mode(RenderMode.MODE_800)
        )
        view_menu.add_command(
            label="ST Mode (F5)", command=lambda: self._set_mode(RenderMode.MODE_ST)
        )
        view_menu.add_command(
            label="Native Mode (F6)", command=lambda: self._set_mode(RenderMode.NATIVE)
        )
        view_menu.add_separator()
        view_menu.add_checkbutton(label="Dithering", command=self._toggle_dithering)
        menubar.add_cascade(label="VIEW", menu=view_menu)

        self.root.config(menu=menubar)

        # Bind keys
        self.root.bind("<F3>", lambda e: self._set_mode(RenderMode.MODE_2600))
        self.root.bind("<F4>", lambda e: self._set_mode(RenderMode.MODE_800))
        self.root.bind("<F5>", lambda e: self._set_mode(RenderMode.MODE_ST))
        self.root.bind("<F6>", lambda e: self._set_mode(RenderMode.NATIVE))
        self.root.bind("<d>", lambda e: self._toggle_dithering())

    def _setup_ui(self) -> None:
        self.canvas = tk.Canvas(self.root, bg="#000033", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.root.bind("<Configure>", self._on_resize)

    def _on_open_file(self) -> None:
        filename = filedialog.askopenfilename(
            initialdir=self.current_path,
            title="Select Image",
            filetypes=(
                ("Image files", "*.png *.jpg *.jpeg *.gif *.bmp *.webp"),
                ("All files", "*.*"),
            ),
        )
        if filename:
            path = Path(filename)
            self.current_path = path.parent
            self._load_and_render_image(path)

    def _set_mode(self, mode: RenderMode) -> None:
        self.state.render_mode = mode
        if self.state.current_image_path:
            self._load_and_render_image(self.state.current_image_path)

    def _toggle_dithering(self) -> None:
        self.state.dithering = not self.state.dithering
        if self.state.current_image_path:
            self._load_and_render_image(self.state.current_image_path)

    def _on_resize(self, event: tk.Event[tk.Misc]) -> None:
        # Debounce or just re-render
        if self.state.current_image_path:
            self._load_and_render_image(self.state.current_image_path)

    def _load_and_render_image(self, path: Path) -> None:
        try:
            self.state.current_image_path = path

            # Target dimensions from canvas
            self.root.update_idletasks()
            w = self.canvas.winfo_width()
            h = self.canvas.winfo_height()

            if w < 10 or h < 10:
                w, h = 800, 600

            context = RenderContext(
                target_width=w,
                target_height=h,
                dithering=self.state.dithering,
                pixel_grid=self.state.pixel_grid,
            )

            transformed = self.pipeline.process(path, self.state.render_mode, context)

            self.tk_image = ImageTk.PhotoImage(transformed)
            self.canvas.delete("all")
            self.canvas.create_image(
                w // 2, h // 2, image=self.tk_image, anchor=tk.CENTER
            )

            self.root.title(f"SafariView - {path.name} [{self.state.render_mode.name}]")

        except Exception as e:
            messagebox.showerror("Error", f"Could not load image: {e}")

    def run(self) -> None:
        self.root.mainloop()


def main() -> int:
    """Launch the Tk frontend through the shared SafariView CLI."""
    from safari_view.main import main as shared_main

    return shared_main(["tk", *sys.argv[1:]])


if __name__ == "__main__":
    main()
