"""EvidencePanel: labeled outcome metrics from the latest evidence (US2, R9).

A BoundContainer over ``evidence_view``: one `label  value` row per metric,
list-valued metrics already enumerated by the selector, status metrics
prefixed with a glyph+label (the non-color counterpart), absent metrics shown
as `n/a`. Latest-artifact-wins; rendering is public-safe per the selector.
"""

from __future__ import annotations

from typing import Any

from rich.text import Text
from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Static

from intui.kit.state.artifacts import EvidenceRow, EvidenceView
from intui.kit.state.model import status_presentation
from intui.viewmodels.selector import Selector
from intui.widgets.bound import BoundContainer


class EvidencePanel(BoundContainer):
    DEFAULT_CSS = """
    EvidencePanel { height: auto; }
    EvidencePanel #evidence-body { padding: 0 1; }
    """

    def __init__(self, selector: Selector[EvidenceView], **kwargs: Any) -> None:
        super().__init__(selector, **kwargs)
        self._view = EvidenceView()

    def compose(self) -> ComposeResult:
        yield VerticalScroll(Static(id="evidence-body"))

    def sync_view(self, vm: EvidenceView) -> None:
        self._view = vm
        self.query_one("#evidence-body", Static).update(self._build_text())

    def _build_text(self) -> Text:
        if not self._view.rows:
            return Text("no evidence")
        theme = getattr(self.app, "intui_theme", None)
        text = Text()
        for row in self._view.rows:
            text.append_text(self._render_row(row, theme))
            text.append("\n")
        return text

    def _render_row(self, row: EvidenceRow, theme: Any) -> Text:
        line = Text()
        if row.status is not None:
            style = status_presentation(row.status)
            color = theme.resolve_color(style.color) if theme is not None else None
            line.append(f"{style.glyph} ", style=color or "")
        value = row.value if row.present and row.value != "" else "n/a"
        line.append(f"{row.label}: ", style="bold")
        line.append(value)
        if row.status is not None:
            line.append(f" [{status_presentation(row.status).label}]")
        return line

    # --- Introspection (apps and tests) -------------------------------------

    def panel_text(self) -> str:
        return self._build_text().plain

    def row_text(self, key: str) -> str:
        theme = getattr(self.app, "intui_theme", None)
        row = next((r for r in self._view.rows if r.key == key), None)
        return "" if row is None else self._render_row(row, theme).plain
