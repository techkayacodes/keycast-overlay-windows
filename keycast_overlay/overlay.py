"""Translucent, click-through Windows keystroke overlay rendered with Tkinter."""

from __future__ import annotations

import queue
import sys
import tkinter as tk
import tkinter.font as tkfont

from .config import OverlayConfig
from .keymap import Chip, KeyStateTracker
from .win_hook import GlobalKeyboardListener, SingleInstanceLock, apply_clickthrough_styles

# Transparent chroma-key background color (never used in chip art)
CHROMA_KEY = "#010203"

# Colors matching keycast-overlay's signature dark-and-gold palette
OLD_BG = "#1c1c1c"
OLD_BORDER = "#3a3a3a"
OLD_FG = "#9a9a9a"

RECENT_BG = "#141414"
RECENT_BORDER = "#d4af37"
RECENT_GLOW = "#7a641d"
RECENT_FG = "#ffffff"

DEMO_KEYS = ("H", "E", "L", "Ctrl+C", "Win+Enter", "Space", "⌫", "Win")
PAUSE_COMBO = "Ctrl+Alt+Shift+P"


def _rounded_rect(
    canvas: tk.Canvas,
    x1: int,
    y1: int,
    x2: int,
    y2: int,
    radius: int,
    **kwargs,
) -> int:
    r = max(1, min(radius, (x2 - x1) // 2, (y2 - y1) // 2))
    points = [
        x1 + r, y1,
        x2 - r, y1,
        x2, y1,
        x2, y1 + r,
        x2, y2 - r,
        x2, y2,
        x2 - r, y2,
        x1 + r, y2,
        x1, y2,
        x1, y2 - r,
        x1, y1 + r,
        x1, y1,
    ]
    return canvas.create_polygon(points, smooth=True, splinesteps=12, **kwargs)


class KeycastOverlayApp:
    """Floating click-through Windows overlay showing recent keystrokes."""

    def __init__(self, config: OverlayConfig) -> None:
        self.config = config
        self.tracker = KeyStateTracker(
            max_keys=config.max_keys,
            highlight=config.highlight,
        )
        self._events: queue.SimpleQueue[tuple[int, bool]] = queue.SimpleQueue()
        self._listener: GlobalKeyboardListener | None = None
        self._lock: SingleInstanceLock | None = None
        self._clear_after_id: str | None = None
        self._paused: bool = False

        self.root = tk.Tk()
        self.root.title("keycast-overlay")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", config.opacity)
        if sys.platform == "win32":
            self.root.attributes("-transparentcolor", CHROMA_KEY)
        self.root.configure(bg=CHROMA_KEY)

        self._font_old = tkfont.Font(
            root=self.root,
            family="Segoe UI",
            size=config.font_size,
            weight="normal",
        )
        self._font_recent = tkfont.Font(
            root=self.root,
            family="Segoe UI",
            size=config.font_size,
            weight="bold",
        )

        self.canvas = tk.Canvas(
            self.root,
            bg=CHROMA_KEY,
            highlightthickness=0,
            bd=0,
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Hide until the first key arrives
        self.root.withdraw()

    def _apply_win32_styles(self) -> None:
        if sys.platform != "win32":
            return
        self.root.update_idletasks()
        hwnd = self.root.winfo_id()
        if hwnd:
            apply_clickthrough_styles(hwnd)

    def _position_window(self, width: int, height: int) -> None:
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        corner = self.config.corner

        if corner.endswith("right"):
            x = max(0, screen_w - width - self.config.margin_right)
        else:
            x = self.config.margin_right

        if corner.startswith("top"):
            y = self.config.margin_top
        else:
            y = max(0, screen_h - height - self.config.margin_top - 40)

        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def redraw(self) -> None:
        chips: list[Chip] = self.tracker.chips()
        self.canvas.delete("all")
        if not chips or self._paused:
            self.root.withdraw()
            return

        pad_x = max(8, int(self.config.font_size * 0.72))
        pad_y = max(4, int(self.config.font_size * 0.36))
        gap = 6
        outer_pad = 4
        radius = 6

        text_h = max(self._font_old.metrics("linespace"), self._font_recent.metrics("linespace"))
        chip_h = text_h + pad_y * 2

        widths: list[int] = []
        for chip in chips:
            font = self._font_recent if chip.recent else self._font_old
            widths.append(font.measure(chip.text) + pad_x * 2)

        total_w = outer_pad * 2 + sum(widths) + gap * (len(chips) - 1)
        total_h = outer_pad * 2 + chip_h

        self.canvas.config(width=total_w, height=total_h)
        self._position_window(total_w, total_h)

        x = outer_pad
        y = outer_pad
        for chip, w in zip(chips, widths):
            if chip.recent:
                # Subtle gold halo ring behind the main gold-bordered pill
                _rounded_rect(
                    self.canvas,
                    x - 1,
                    y - 1,
                    x + w + 1,
                    y + chip_h + 1,
                    radius + 1,
                    fill="",
                    outline=RECENT_GLOW,
                    width=2,
                )
                _rounded_rect(
                    self.canvas,
                    x,
                    y,
                    x + w,
                    y + chip_h,
                    radius,
                    fill=RECENT_BG,
                    outline=RECENT_BORDER,
                    width=1.5,
                )
                self.canvas.create_text(
                    x + w / 2,
                    y + chip_h / 2,
                    text=chip.text,
                    fill=RECENT_FG,
                    font=self._font_recent,
                )
            else:
                _rounded_rect(
                    self.canvas,
                    x,
                    y,
                    x + w,
                    y + chip_h,
                    radius,
                    fill=OLD_BG,
                    outline=OLD_BORDER,
                    width=1,
                )
                self.canvas.create_text(
                    x + w / 2,
                    y + chip_h / 2,
                    text=chip.text,
                    fill=OLD_FG,
                    font=self._font_old,
                )
            x += w + gap

        self.root.deiconify()
        self.root.attributes("-topmost", True)
        self._apply_win32_styles()

    def _schedule_clear(self) -> None:
        if self._clear_after_id is not None:
            self.root.after_cancel(self._clear_after_id)
            self._clear_after_id = None
        if self.config.clear_after > 0:
            delay_ms = int(self.config.clear_after * 1000)
            self._clear_after_id = self.root.after(delay_ms, self._clear_keys)

    def _clear_keys(self) -> None:
        self._clear_after_id = None
        self.tracker.clear()
        self.redraw()

    def _poll_events(self) -> None:
        changed = False
        while True:
            try:
                vk_code, pressed = self._events.get_nowait()
            except queue.Empty:
                break
            emitted = self.tracker.handle_vk(vk_code, pressed)
            if emitted == PAUSE_COMBO:
                self._paused = not self._paused
                self.tracker.clear()
                changed = True
            elif emitted is not None and not self._paused:
                changed = True

        if changed:
            self.redraw()
            if not self._paused:
                self._schedule_clear()

        self.root.after(16, self._poll_events)

    def run(self) -> int:
        if not self.config.demo and sys.platform == "win32":
            self._lock = SingleInstanceLock()
            if not self._lock.acquire():
                self.root.destroy()
                return 0

        try:
            if self.config.demo:
                for key in DEMO_KEYS:
                    self.tracker.push(key)
                self.redraw()
            else:
                if sys.platform != "win32":
                    raise RuntimeError("Live key capture requires Windows (use --demo to preview).")
                self._listener = GlobalKeyboardListener(
                    lambda vk, pressed: self._events.put((vk, pressed))
                )
                self._listener.start()
                self.root.after(16, self._poll_events)

            self.root.mainloop()
            return 0
        finally:
            if self._listener is not None:
                self._listener.stop()
            if self._lock is not None:
                self._lock.release()
