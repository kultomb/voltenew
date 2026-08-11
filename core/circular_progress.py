"""
Vòng tiến trình tròn — canvas, có % giữa và cung quay khi đang quét.
"""

from __future__ import annotations

import tkinter as tk

import customtkinter as ctk

from core.ui_theme import C, get_font


class CircularProgress(ctk.CTkFrame):
    def __init__(
        self,
        master,
        *,
        size: int = 136,
        line_width: int = 7,
        track_color: str | None = None,
        progress_color: str | None = None,
        spin_color: str | None = None,
        bg: str | None = None,
    ):
        super().__init__(master, fg_color="transparent")
        self._size = size
        self._line = line_width
        self._track = track_color or C["border_subtle"]
        self._prog = progress_color or C["accent"]
        self._spin = spin_color or C["accent_muted"]
        self._bg = bg or C["bg_modal"]
        self._fraction = 0.0
        self._spin_deg = 0.0
        self._animating = False
        self._anim_id: str | None = None

        self._canvas = tk.Canvas(
            self,
            width=size,
            height=size,
            highlightthickness=0,
            bd=0,
            bg=self._bg,
        )
        self._canvas.pack()
        self._redraw()

    def set_progress(self, fraction: float) -> None:
        self._fraction = max(0.0, min(1.0, float(fraction)))
        self._redraw()

    def start_animation(self) -> None:
        if self._animating:
            return
        self._animating = True
        self._tick()

    def stop_animation(self) -> None:
        self._animating = False
        if self._anim_id is not None:
            try:
                self.after_cancel(self._anim_id)
            except Exception:
                pass
            self._anim_id = None

    def set_complete(self) -> None:
        self.stop_animation()
        self.set_progress(1.0)

    def _tick(self) -> None:
        if not self._animating or not self.winfo_exists():
            return
        self._spin_deg = (self._spin_deg + 4.5) % 360
        self._redraw()
        self._anim_id = self.after(28, self._tick)

    def _redraw(self) -> None:
        if not self._canvas.winfo_exists():
            return
        c = self._size / 2
        pad = self._line / 2 + 2
        r = c - pad
        cv = self._canvas
        cv.delete("all")

        cv.create_oval(
            c - r, c - r, c + r, c + r,
            outline=self._track,
            width=self._line,
        )

        if self._fraction > 0.001:
            extent = -360 * self._fraction
            cv.create_arc(
                c - r, c - r, c + r, c + r,
                start=90,
                extent=extent,
                style=tk.ARC,
                outline=self._prog,
                width=self._line,
            )

        if self._animating and self._fraction < 0.995:
            sweep = 72
            start = 90 - self._spin_deg
            cv.create_arc(
                c - r, c - r, c + r, c + r,
                start=start,
                extent=-sweep,
                style=tk.ARC,
                outline=self._spin,
                width=max(3, self._line - 2),
            )

        pct = int(round(self._fraction * 100))
        cv.create_text(
            c, c - 6,
            text=f"{pct}%",
            fill=C["text_primary"],
            font=("Segoe UI", 20, "bold"),
        )
        cv.create_text(
            c, c + 16,
            text="AI Scan",
            fill=C["text_tertiary"],
            font=get_font("caption"),
        )

    def destroy(self) -> None:
        self.stop_animation()
        super().destroy()
