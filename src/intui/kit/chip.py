"""TaskCounterChip: glanceable progress with expandable task list (US1).

Collapsed: ``7 / 14 tasks complete`` (narrow fallback ``7/14``; empty state
``no tasks``). Expanded: a scrollable task list with glyph+label status
indicators and a counts-by-status footer. Expansion is local UI state
(research R5) — keyboard (enter/space) and mouse both toggle it.
"""

from __future__ import annotations

from typing import Any

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Static

from intui.kit.state.model import CORE_STATUSES, status_presentation
from intui.kit.state.selectors import ChipView
from intui.viewmodels.selector import Selector
from intui.widgets.bound import BoundContainer

_NARROW_WIDTH = 30


class TaskCounterChip(BoundContainer):
    BINDINGS = [("enter,space", "toggle", "Tasks")]

    can_focus = True

    DEFAULT_CSS = """
    TaskCounterChip { height: auto; max-height: 16; }
    TaskCounterChip:focus #chip-header { text-style: bold reverse; }
    TaskCounterChip #chip-list { height: auto; max-height: 12; display: none; }
    TaskCounterChip #chip-footer { display: none; color: $text-muted; }
    TaskCounterChip.expanded #chip-list { display: block; }
    TaskCounterChip.expanded #chip-footer { display: block; }
    """

    def __init__(self, selector: Selector[ChipView], **kwargs: Any) -> None:
        super().__init__(selector, **kwargs)
        self._vm = ChipView()
        self.expanded = False

    def compose(self) -> ComposeResult:
        yield Static(id="chip-header")
        yield VerticalScroll(Static(id="chip-rows"), id="chip-list")
        yield Static(id="chip-footer")

    # --- BoundContainer contract --------------------------------------------

    def sync_view(self, vm: ChipView) -> None:
        self._vm = vm
        self._render_all()

    def on_resize(self) -> None:
        self._render_all()

    # --- Interaction ---------------------------------------------------------

    def action_toggle(self) -> None:
        self.expanded = not self.expanded
        self.set_class(self.expanded, "expanded")
        self._render_all()

    def on_click(self) -> None:
        self.action_toggle()

    # --- Rendering -----------------------------------------------------------

    def _render_all(self) -> None:
        self.query_one("#chip-header", Static).update(self.header_text())
        if self.expanded:
            self.query_one("#chip-rows", Static).update("\n".join(self.row_texts()))
            self.query_one("#chip-footer", Static).update(self.footer_text())

    def header_text(self) -> str:
        affordance = "▾" if self.expanded else "▸"
        vm = self._vm
        if vm.total == 0:
            return f"{affordance} no tasks"
        long_form = f"{affordance} {vm.completed} / {vm.total} tasks complete"
        width = self.size.width or self.app.size.width
        if width and len(long_form) + 4 > width:
            return f"{affordance} {vm.completed}/{vm.total}"
        return long_form

    def row_texts(self) -> list[str]:
        return [f"{row.glyph} {row.label:<8} {row.title}" for row in self._vm.rows]

    def footer_text(self) -> str:
        parts = []
        for status in (*CORE_STATUSES, "other"):
            count = self._vm.status_counts.get(status, 0)
            if count:
                label = status_presentation(status).label if status != "other" else "other"
                parts.append(f"{count} {label}")
        return " · ".join(parts)

    def header_widget(self) -> Static:
        return self.query_one("#chip-header", Static)
