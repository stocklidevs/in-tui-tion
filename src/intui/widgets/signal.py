"""The Signal primitive: a status-driven activity indicator (Principle V).

Appearance — color, motion (including the KITT-style swoosh), glyph, and
label — derives exclusively from the bound status selector and the declared
status->style mapping. The widget is never set directly, and every status
keeps its textual counterpart even with color disabled (SC-006).
"""

from __future__ import annotations

from typing import Any

from rich.text import Text

from intui.theming.signal_style import MotionMode, StatusStyle, resolve_status_style
from intui.theming.theme import Theme
from intui.viewmodels.selector import Selector
from intui.widgets.bound import BoundWidget

_FPS = 12.0


class Signal(BoundWidget):
    """Status indicator: ``[animated track] glyph label``."""

    DEFAULT_CSS = """
    Signal { height: 1; width: auto; }
    """

    def __init__(
        self,
        selector: Selector[str],
        styles: dict[str, StatusStyle],
        *,
        track_width: int = 10,
        **kwargs: Any,
    ) -> None:
        super().__init__(selector, **kwargs)
        self._styles = dict(styles)
        self._track_width = max(track_width, 3)
        self._frame = 0
        self._status = ""

    # --- BoundWidget contract ----------------------------------------------

    def render_view(self, vm: str) -> Text:
        self._status = vm
        return self._render_frame()

    # --- Animation -----------------------------------------------------------

    def on_mount(self) -> None:
        super().on_mount()
        self.set_interval(1.0 / _FPS, self._tick)

    def _tick(self) -> None:
        style = self._current_style()
        if style.motion is MotionMode.STEADY:
            return
        self._frame += 1
        self.update(self._render_frame())

    # --- Introspection -------------------------------------------------------

    def current_motion(self) -> MotionMode:
        """The motion mode of the bound status's current style."""
        return self._current_style().motion

    def plain_text(self) -> str:
        """Color-free rendered text (track + glyph + label)."""
        return self._render_frame().plain

    # --- Rendering -----------------------------------------------------------

    def _current_style(self) -> StatusStyle:
        return resolve_status_style(self._status, self._styles)

    def _theme(self) -> Theme | None:
        return getattr(self.app, "intui_theme", None) if self.is_attached else None

    def _render_frame(self) -> Text:
        style = self._current_style()
        theme = self._theme()
        color = theme.resolve_color(style.color) if theme is not None else None

        track = self._render_track(style)
        text = Text()
        text.append(track, style=color or "")
        text.append("  ")
        text.append(style.glyph, style=f"bold {color}" if color else "bold")
        text.append(f" {style.label}")
        return text

    def _render_track(self, style: StatusStyle) -> str:
        width = self._track_width
        if style.motion is MotionMode.STEADY:
            return "▰" * width
        if style.motion is MotionMode.PULSE:
            return ("▰" if (self._frame // int(_FPS / 2)) % 2 == 0 else "▱") * width
        if style.motion is MotionMode.STROBE:
            return ("█" if self._frame % 2 else " ") * width
        # SWOOSH: a bright head sweeping back and forth across the track.
        period = 2 * (width - 1)
        pos = self._frame % period
        head = pos if pos < width else period - pos
        cells = ["·"] * width
        for offset, char in ((2, "▪"), (1, "▮"), (0, "█")):
            tail = head - offset if pos < width else head + offset
            if 0 <= tail < width:
                cells[tail] = char
        return "".join(cells)
