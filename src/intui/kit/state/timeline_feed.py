"""Run timeline feed: merge conversation + taskboard into one ordered column.

Engine-free presentation model. The console renders these rows top-to-bottom;
each row is self-describing (glyph + label + text) so status never relies on
color alone (Principle IV).
"""

from __future__ import annotations

from dataclasses import dataclass

from intui.state.snapshot import Snapshot
from intui.viewmodels.selector import Selector, selector

STATUS_GLYPH: dict[str, str] = {
    "passed": "✓",
    "completed": "✓",
    "failed": "✗",
    "running": "◷",
    "started": "◷",
    "skipped": "◌",
    "blocked": "⊘",
}
_FALLBACK_GLYPH = "◆"


@dataclass(frozen=True, slots=True)
class TimelineRow:
    order: int
    kind: str  # "message" | "task" | "failure" | "milestone"
    glyph: str
    label: str
    text: str
    status: str
    ref: str  # work item / diff reference for failures, else ""


@dataclass(frozen=True, slots=True)
class TimelineFeedView:
    rows: tuple[TimelineRow, ...] = ()


def _glyph_for(status: str) -> str:
    return STATUS_GLYPH.get(status, _FALLBACK_GLYPH)


def run_timeline_view() -> Selector[TimelineFeedView]:
    """A memoized selector producing the ordered feed for the console."""

    @selector
    def _run_timeline(snapshot: Snapshot) -> TimelineFeedView:
        return _build_feed(snapshot)

    return _run_timeline


def _build_feed(snapshot: Snapshot) -> TimelineFeedView:
    rows: list[TimelineRow] = []
    order = 0

    board = snapshot.slice("taskboard")
    for item in board.work_items.values():
        status = str(item.status)
        kind = "failure" if status == "failed" else "task"
        rows.append(
            TimelineRow(
                order=order,
                kind=kind,
                glyph="✗" if kind == "failure" else _glyph_for(status),
                label=status or "task",
                text=str(item.title),
                status=status,
                ref=str(item.work_item_id),
            )
        )
        order += 1

    convo = snapshot.slice("conversation")
    for entry in convo.entries:
        text = str(entry.text)
        is_fail = "FAILED" in text
        rows.append(
            TimelineRow(
                order=order,
                kind="failure" if is_fail else "message",
                glyph="✗" if is_fail else "›",
                label=str(entry.role) or "system",
                text=text,
                status="failed" if is_fail else "",
                ref="",
            )
        )
        order += 1

    return TimelineFeedView(rows=tuple(rows))
