"""Modal panel overlays: a browsable panel over the timeline, Esc or ✕ closes.

The timeline is home base; the rich panels (files / metrics / lanes /
evidence / tasks) are transient overlays reached by key or slash command
(the approved "inline diffs + overlays" blend). The title bar carries a
clickable ✕ so mouse users have a visible way out alongside Esc.
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widget import Widget
from textual.widgets import Static


class _CloseButton(Static):
    """A one-cell clickable close affordance for the overlay title bar."""

    DEFAULT_CSS = """
    _CloseButton { width: auto; color: $text-muted; }
    _CloseButton:hover { color: $text; text-style: bold; }
    """

    def on_click(self) -> None:
        screen = self.screen
        if isinstance(screen, PanelOverlay):
            screen.action_close_overlay()


class PanelOverlay(ModalScreen[None]):
    DEFAULT_CSS = """
    PanelOverlay { align: center middle; }
    PanelOverlay > #overlay-frame {
        width: 80%; height: 80%;
        border: round $accent; padding: 0 2 1 2; background: $surface;
    }
    PanelOverlay #overlay-bar { height: 1; }
    PanelOverlay #overlay-title { width: 1fr; text-style: bold; color: $text-muted; }
    """
    BINDINGS = [("escape", "close_overlay", "Close")]

    def __init__(self, title: str, panel: Widget) -> None:
        super().__init__()
        self._title = title
        self._panel = panel

    def compose(self) -> ComposeResult:
        bar = Horizontal(
            Static(self._title, id="overlay-title"),
            _CloseButton("✕ close", id="overlay-close"),
            id="overlay-bar",
        )
        yield Vertical(bar, self._panel, id="overlay-frame")

    def action_close_overlay(self) -> None:
        self.dismiss(None)
