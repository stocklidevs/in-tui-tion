"""LanesPanel: concurrent workers as independent lanes (US3).

One row per worker — an animated Signal (steady once terminal, so finished
lanes stop animating), the worker name, current activity, and last result.
Each lane's Signal binds to a per-lane status selector, so lanes update
independently as interleaved events arrive. The panel can be scoped to a
parent task (FR-012).
"""

from __future__ import annotations

from typing import Any

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Static

from intui.kit.state.selectors import LaneRow, LanesView, lane_status_view
from intui.theming.signal_style import MotionMode, StatusStyle
from intui.viewmodels.selector import Selector
from intui.widgets.bound import BoundContainer
from intui.widgets.signal import Signal

# Lane statuses: only "active" animates; every terminal state is steady so a
# finished lane visibly stops moving (US3-3).
LANE_SIGNAL_STYLES: dict[str, StatusStyle] = {
    "pending": StatusStyle(color="muted", motion=MotionMode.STEADY, glyph="·", label="pending"),
    "active": StatusStyle(color="thinking", motion=MotionMode.SWOOSH, glyph="»", label="active"),
    "completed": StatusStyle(color="success", motion=MotionMode.STEADY, glyph="✔", label="done"),
    "failed": StatusStyle(color="failure", motion=MotionMode.STEADY, glyph="✘", label="failed"),
}


class LaneWidget(Horizontal):
    """A single lane row: Signal + textual detail."""

    DEFAULT_CSS = """
    LaneWidget { height: 1; }
    LaneWidget Signal { width: auto; margin: 0 1 0 0; }
    LaneWidget .lane-text { width: 1fr; }
    """

    def __init__(self, row: LaneRow, slice_name: str, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._row = row
        self._slice_name = slice_name

    def compose(self) -> ComposeResult:
        yield Signal(
            lane_status_view(self._row.key, self._slice_name),
            LANE_SIGNAL_STYLES,
            track_width=6,
        )
        yield Static(self._text(), classes="lane-text")

    def update_row(self, row: LaneRow) -> None:
        self._row = row
        self.query_one(".lane-text", Static).update(self._text())

    def _text(self) -> str:
        parts = [self._row.name]
        if self._row.activity:
            parts.append(self._row.activity)
        if self._row.last_summary and self._row.last_summary != self._row.activity:
            parts.append(self._row.last_summary)
        return "  ".join(parts)

    @property
    def signal(self) -> Signal:
        return self.query_one(Signal)

    def full_text(self) -> str:
        """Signal label + textual detail (color-free), for inspection/tests."""
        return f"{self.signal.plain_text()}  {self._text()}"


class LanesPanel(BoundContainer):
    DEFAULT_CSS = """
    LanesPanel { height: auto; }
    """

    def __init__(
        self,
        selector: Selector[LanesView],
        *,
        slice_name: str = "taskboard",
        **kwargs: Any,
    ) -> None:
        super().__init__(selector, **kwargs)
        self._slice_name = slice_name
        self._rows: dict[str, LaneWidget] = {}

    def sync_view(self, vm: LanesView) -> None:
        present = {lane.key for lane in vm.lanes}
        for key in list(self._rows):
            if key not in present:
                self._rows.pop(key).remove()
        for lane in vm.lanes:
            existing = self._rows.get(lane.key)
            if existing is not None:
                existing.update_row(lane)
            else:
                widget = LaneWidget(lane, self._slice_name)
                self._rows[lane.key] = widget
                self.mount(widget)

    # --- Introspection (apps and tests) -------------------------------------

    def lane_texts(self) -> list[str]:
        return [w.full_text() for w in self._rows.values()]

    def lane_text_for(self, key: str) -> str:
        return self._rows[key].full_text()

    def lane_motion(self, key: str) -> MotionMode:
        return self._rows[key].signal.current_motion()
