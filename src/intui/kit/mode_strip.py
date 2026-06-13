"""ModeStrip: a row of modes with the active one marked (US1, R13).

Renders ``mode_view`` as a compact row; the active mode is marked with a `▸`
(the non-color counterpart) plus emphasis. Optional shortcut keys are
registered app-globally (via ``IntuiApp.bind_key``) and post a ``switch_mode``
intent — so mode switching flows intent → event → state.
"""

from __future__ import annotations

from collections.abc import Mapping
from functools import partial
from typing import TYPE_CHECKING, Any, cast

from rich.text import Text
from textual.widgets import Static

from intui.kit.state.modes import ModeView, switch_mode_intent
from intui.viewmodels.selector import Selector
from intui.widgets.bound import BoundContainer

if TYPE_CHECKING:
    from intui.app import IntuiApp


class ModeStrip(BoundContainer):
    DEFAULT_CSS = """
    ModeStrip { height: 1; }
    ModeStrip Static { height: 1; }
    """

    def __init__(
        self,
        selector: Selector[ModeView],
        keys: Mapping[str, str] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(selector, **kwargs)
        self._view = ModeView()
        self._keys = dict(keys or {})

    def compose(self) -> Any:
        yield Static(id="mode-row")

    def on_mount(self) -> None:
        super().on_mount()
        app = cast("IntuiApp", self.app)
        for key, mode in self._keys.items():
            app.bind_key(key, partial(self._switch, mode), description=f"Mode: {mode}")

    def _switch(self, mode: str) -> None:
        cast("IntuiApp", self.app).post_intent(switch_mode_intent(mode))

    def sync_view(self, vm: ModeView) -> None:
        self._view = vm
        self.query_one("#mode-row", Static).update(self._build_text())

    def _build_text(self) -> Text:
        theme = getattr(self.app, "intui_theme", None)
        accent = theme.resolve_color("accent") if theme is not None else None
        text = Text()
        for i, entry in enumerate(self._view.entries):
            if i:
                text.append("  ")
            label = f"▸ {entry.name}" if entry.active else f"  {entry.name}"
            text.append(label, style=(f"bold {accent}" if entry.active and accent else ""))
        return text

    def strip_text(self) -> str:
        return self._build_text().plain
