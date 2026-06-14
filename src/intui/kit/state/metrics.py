"""Process metrics: status + resource usage reduced from metric events.

Engine-free. A monitored (or self-reporting) process emits ``process_started`` /
``metric_sample`` / ``process_exited``; this reduces them into current + peak
usage, status, duration, and a bounded recent-sample history, and projects a
view with human-readable values, a status glyph/label, and CPU/memory
sparklines. Public-safe (the command label is redacted by default), like the
diff/evidence/file views.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Any

from intui.events.envelope import Event
from intui.kit.state.artifacts import redact
from intui.kit.state.model import status_presentation
from intui.state.snapshot import Snapshot
from intui.viewmodels.selector import Selector

#: Canonical metric event types (stream contract).
METRICS_EVENT_TYPES = frozenset({"process_started", "metric_sample", "process_exited"})

_DEFAULT_WINDOW = 60
_SPARK_TICKS = "▁▂▃▄▅▆▇█"

# Metric status -> the shared status presentation vocabulary (glyph + label).
_STATUS_PRESENTATION = {
    "idle": "pending",
    "running": "active",
    "passed": "completed",
    "failed": "failed",
}


# --- Models ------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class MetricsSample:
    cpu_percent: float
    rss_bytes: int
    elapsed_ms: int


@dataclass(frozen=True, slots=True)
class MetricsState:
    label: str = ""
    status: str = "idle"
    cpu_percent: float = 0.0
    rss_bytes: int = 0
    peak_rss_bytes: int = 0
    elapsed_ms: int = 0
    exit_code: int | None = None
    samples: tuple[MetricsSample, ...] = ()
    window: int = _DEFAULT_WINDOW


@dataclass(frozen=True, slots=True)
class MetricsView:
    present: bool = False
    label: str = ""
    status: str = "idle"
    glyph: str = ""
    status_label: str = ""
    cpu_percent: float = 0.0
    rss_human: str = "0 B"
    peak_human: str = "0 B"
    duration_human: str = "0.0s"
    cpu_spark: str = ""
    mem_spark: str = ""
    sample_count: int = 0


# --- Reduction ---------------------------------------------------------------


def metrics_slice(window: int = _DEFAULT_WINDOW) -> tuple[Any, MetricsState]:
    """``(reducer, initial)`` for ``compose_reducers(metrics=metrics_slice())``."""

    def reduce(state: MetricsState, event: Event) -> MetricsState:
        if event.type == "process_started":
            label = str(event.payload.get("label", ""))
            return MetricsState(label=label, status="running", window=window)
        if event.type == "metric_sample":
            sample = MetricsSample(
                cpu_percent=float(event.payload.get("cpu_percent", 0.0) or 0.0),
                rss_bytes=int(event.payload.get("rss_bytes", 0) or 0),
                elapsed_ms=int(event.payload.get("elapsed_ms", 0) or 0),
            )
            samples = (*state.samples, sample)[-window:]
            return replace(
                state,
                cpu_percent=sample.cpu_percent,
                rss_bytes=sample.rss_bytes,
                peak_rss_bytes=max(state.peak_rss_bytes, sample.rss_bytes),
                elapsed_ms=sample.elapsed_ms,
                samples=samples,
            )
        if event.type == "process_exited":
            exit_code = event.payload.get("exit_code")
            if event.status in ("passed", "failed"):
                status = event.status
            else:
                status = "passed" if int(exit_code or 0) == 0 else "failed"
            duration = int(event.payload.get("duration_ms", state.elapsed_ms) or state.elapsed_ms)
            return replace(
                state,
                status=status,
                exit_code=int(exit_code) if exit_code is not None else state.exit_code,
                elapsed_ms=duration,
            )
        return state

    return reduce, MetricsState(window=window)


# --- View model + selector ---------------------------------------------------


def metrics_view(
    slice_name: str = "metrics", *, public_safe: bool = True
) -> Selector[MetricsView]:
    def project(snapshot: Snapshot) -> MetricsView:
        state: MetricsState = snapshot.slice(slice_name)
        if state.status == "idle" and not state.samples and not state.label:
            return MetricsView()
        style = status_presentation(_STATUS_PRESENTATION.get(state.status, state.status))
        label = redact(state.label) if public_safe else state.label
        return MetricsView(
            present=True,
            label=label,
            status=state.status,
            glyph=style.glyph,
            status_label=state.status,
            cpu_percent=state.cpu_percent,
            rss_human=human_bytes(state.rss_bytes),
            peak_human=human_bytes(state.peak_rss_bytes),
            duration_human=_human_duration(state.elapsed_ms),
            cpu_spark=sparkline([s.cpu_percent for s in state.samples]),
            mem_spark=sparkline([s.rss_bytes for s in state.samples]),
            sample_count=len(state.samples),
        )

    return Selector(project)


# --- Pure helpers ------------------------------------------------------------


def sparkline(values: Sequence[float]) -> str:
    """Render values as a ``▁▂▃▄▅▆▇█`` sparkline, scaled to the max."""
    nums = [float(v) for v in values]
    if not nums:
        return ""
    hi = max(nums)
    if hi <= 0:
        return _SPARK_TICKS[0] * len(nums)
    last = len(_SPARK_TICKS) - 1
    return "".join(_SPARK_TICKS[min(last, int(v / hi * last))] for v in nums)


def human_bytes(n: int) -> str:
    """Human-readable byte count, e.g. ``48.2 MB``."""
    size = float(n)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024 or unit == "TB":
            if unit == "B":
                return f"{int(size)} B"
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


def _human_duration(ms: int) -> str:
    seconds = ms / 1000
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes, secs = divmod(int(seconds), 60)
    return f"{minutes:02d}:{secs:02d}"
