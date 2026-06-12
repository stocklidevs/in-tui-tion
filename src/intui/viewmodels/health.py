"""Built-in stream-health view model (FR-007)."""

from __future__ import annotations

from dataclasses import dataclass

from intui.events.stream import StreamState
from intui.state.snapshot import Snapshot
from intui.viewmodels.selector import Selector

_LABELS = {
    StreamState.LIVE: "live",
    StreamState.ENDED: "stream ended",
    StreamState.DISCONNECTED: "disconnected",
    StreamState.ERRORING: "erroring",
}


@dataclass(frozen=True, slots=True)
class HealthView:
    state: StreamState
    label: str
    rejected_count: int
    duplicate_count: int
    last_error_summary: str | None


def _health_view(snapshot: Snapshot) -> HealthView:
    health = snapshot.health
    error = health.last_error
    summary = None if error is None else f"event {error.event_id or '?'}: {error.reason}"
    return HealthView(
        state=health.state,
        label=_LABELS[health.state],
        rejected_count=health.rejected_count,
        duplicate_count=health.duplicate_count,
        last_error_summary=summary,
    )


health_view: Selector[HealthView] = Selector(_health_view)
