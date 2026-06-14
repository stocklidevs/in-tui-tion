"""MetricsPanel: process status + resource usage + sparklines (R-metrics).

A bound widget projecting :func:`metrics_view` — status (non-color glyph +
label), wall-clock duration, CPU %, current/peak memory, and CPU/memory
sparklines. State-derived (Principle I); refreshes as samples arrive.
"""

from __future__ import annotations

from typing import Any

from textual.app import ComposeResult
from textual.widgets import Static

from intui.kit.state.metrics import MetricsView
from intui.viewmodels.selector import Selector
from intui.widgets.bound import BoundContainer


class MetricsPanel(BoundContainer):
    DEFAULT_CSS = """
    MetricsPanel { height: auto; padding: 0 1; }
    MetricsPanel #metrics-head { height: auto; }
    MetricsPanel #metrics-spark { height: auto; color: $text-muted; }
    """

    def __init__(self, selector: Selector[MetricsView], **kwargs: Any) -> None:
        super().__init__(selector, **kwargs)
        self._vm = MetricsView()

    def compose(self) -> ComposeResult:
        yield Static(id="metrics-head")
        yield Static(id="metrics-spark")

    # --- BoundContainer contract --------------------------------------------

    def sync_view(self, vm: MetricsView) -> None:
        self._vm = vm
        self.query_one("#metrics-head", Static).update(self._head_text())
        self.query_one("#metrics-spark", Static).update(self._spark_text())

    def _head_text(self) -> str:
        vm = self._vm
        if not vm.present:
            return "no process — run one with `intui watch --metrics -- <cmd>`"
        return (
            f"{vm.glyph} {vm.status_label}  ·  {vm.label}  ·  {vm.duration_human}"
            f"  ·  CPU {vm.cpu_percent:.0f}%"
            f"  ·  mem {vm.rss_human} / {vm.peak_human}"
        )

    def _spark_text(self) -> str:
        vm = self._vm
        if not vm.present or not vm.cpu_spark:
            return ""
        return f"cpu {vm.cpu_spark}   mem {vm.mem_spark}"

    # --- Introspection (apps and tests) -------------------------------------

    def summary_text(self) -> str:
        head = self._head_text()
        spark = self._spark_text()
        return f"{head}\n{spark}" if spark else head

    def status(self) -> str:
        return self._vm.status
