"""Modal panel overlays: a browsable panel over the timeline, Esc to close.

The timeline is home base; the rich panels (files / metrics / lanes /
evidence / tasks) are transient overlays reached by key or slash command
(the approved "inline diffs + overlays" blend).
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widget import Widget


class PanelOverlay(ModalScreen[None]):
    DEFAULT_CSS = """
    PanelOverlay { align: center middle; }
    PanelOverlay > #overlay-frame {
        width: 80%; height: 80%;
        border: round $accent; padding: 1 2; background: $surface;
    }
    """
    BINDINGS = [("escape", "close_overlay", "Close")]

    def __init__(self, title: str, panel: Widget) -> None:
        super().__init__()
        self._title = title
        self._panel = panel

    def compose(self) -> ComposeResult:
        frame = Vertical(self._panel, id="overlay-frame")
        frame.border_title = self._title
        yield frame

    def action_close_overlay(self) -> None:
        self.dismiss(None)
