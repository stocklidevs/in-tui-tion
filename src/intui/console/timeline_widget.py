"""RunTimeline: the single-column run feed (replaces the side chat window).

Renders :func:`intui.kit.state.run_timeline_view` rows top-to-bottom in
arrival order — messages, task results, and failure callouts in one column.
Every row carries its glyph + label (Principle IV); auto-scrolls to the
latest entries.
"""

from __future__ import annotations

from typing import Any

from rich.text import Text
from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Static

from intui.kit.state import TimelineFeedView
from intui.viewmodels.selector import Selector
from intui.widgets.bound import BoundContainer


class RunTimeline(BoundContainer):
    DEFAULT_CSS = """
    RunTimeline { height: 1fr; }
    RunTimeline #timeline-scroll { height: 1fr; }
    RunTimeline #timeline-body { padding: 0 1; }
    """

    def __init__(self, selector: Selector[TimelineFeedView], **kwargs: Any) -> None:
        super().__init__(selector, **kwargs)
        self._view = TimelineFeedView()

    def compose(self) -> ComposeResult:
        yield VerticalScroll(Static(id="timeline-body"), id="timeline-scroll")

    def sync_view(self, vm: TimelineFeedView) -> None:
        self._view = vm
        self.query_one("#timeline-body", Static).update(self._build_text())
        self.query_one("#timeline-scroll", VerticalScroll).scroll_end(animate=False)

    def _build_text(self) -> Text:
        if not self._view.rows:
            return Text("waiting for events…", style="dim")
        try:
            theme = getattr(self.app, "intui_theme", None)
        except Exception:  # noqa: BLE001 - rendered outside a running app (unit tests)
            theme = None
        text = Text()
        for i, row in enumerate(self._view.rows):
            if i:
                text.append("\n")
            color = self._row_color(theme, row.status)
            text.append(f"{row.glyph} ", style=color or "")
            text.append(row.text)
            if row.label and row.kind in ("task", "failure"):
                text.append(f"  [{row.label}]", style="dim")
        return text

    def _row_color(self, theme: Any, status: str) -> str | None:
        if theme is None:
            return None
        key = {"failed": "failure", "completed": "success", "passed": "success"}.get(status)
        return str(theme.resolve_color(key)) if key else None

    def log_text(self) -> str:
        return self._build_text().plain
