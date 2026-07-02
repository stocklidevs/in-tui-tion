"""Run timeline feed: the stream reduced into one chronological column.

Engine-free. Unlike the panel slices (which index by task/artifact), this
reducer preserves **arrival order**: rows appear in the order their events
arrived, so the console's timeline reads top-to-bottom the way the run
happened. Work items and tasks are single rows updated in place (started →
completed keeps the start position); failure detail messages (``FAILED …``)
attach to their failure row as callout detail instead of floating away as
unrelated lines. Every row carries a glyph + label so status never relies on
color alone (Principle IV).
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any

from intui.events.envelope import Event
from intui.state.snapshot import Snapshot
from intui.viewmodels.selector import Selector, selector

STATUS_GLYPH: dict[str, str] = {
    "passed": "✓",
    "completed": "✓",
    "failed": "✗",
    "active": "◷",
    "running": "◷",
    "started": "◷",
    "pending": "◌",
    "skipped": "◌",
    "blocked": "⊘",
}
_FALLBACK_GLYPH = "◆"

#: Event types the timeline reducer consumes (all already canonical).
TIMELINE_EVENT_TYPES = frozenset(
    {
        "run_started",
        "run_completed",
        "run_failed",
        "task_created",
        "task_started",
        "task_blocked",
        "task_completed",
        "work_item_started",
        "work_item_completed",
        "message_added",
        "question_requested",
        "approval_requested",
    }
)


@dataclass(frozen=True, slots=True)
class TimelineRow:
    order: int
    kind: str  # "message" | "task" | "failure" | "milestone"
    glyph: str
    label: str
    text: str
    status: str
    ref: str  # task/work-item reference for updates + failure matching
    detail: str = ""  # attached failure detail (rendered as a callout)


@dataclass(frozen=True, slots=True)
class TimelineFeedView:
    rows: tuple[TimelineRow, ...] = ()


@dataclass(frozen=True, slots=True)
class TimelineState:
    rows: tuple[TimelineRow, ...] = ()


def _glyph_for(status: str) -> str:
    return STATUS_GLYPH.get(status, _FALLBACK_GLYPH)


def timeline_slice() -> tuple[Any, TimelineState]:
    """``(reducer, initial)`` for ``compose_reducers(timeline=...)``."""
    return _reduce, TimelineState()


def _reduce(state: TimelineState, event: Event) -> TimelineState:
    if event.type in ("work_item_started", "work_item_completed"):
        return _reduce_scoped(state, event, ref=event.scope.work_item_id)
    if event.type in ("task_created", "task_started", "task_blocked", "task_completed"):
        return _reduce_scoped(state, event, ref=event.scope.task_id)
    if event.type in ("message_added", "question_requested", "approval_requested"):
        return _reduce_message(state, event)
    if event.type in ("run_started", "run_completed", "run_failed"):
        return _reduce_milestone(state, event)
    return state


def _append(state: TimelineState, row: TimelineRow) -> TimelineState:
    return replace(state, rows=(*state.rows, row))


def _status_of(event: Event) -> str:
    by_type = {
        "task_created": "pending",
        "task_started": "active",
        "task_blocked": "blocked",
        "work_item_started": "active",
    }
    if event.type in by_type:
        return by_type[event.type]
    return "failed" if event.status == "failed" else "completed"


def _title_of(event: Event, fallback: str) -> str:
    name = event.payload.get("name")
    if isinstance(name, str) and name:
        return name
    if event.summary:
        return event.summary
    return fallback


def _reduce_scoped(state: TimelineState, event: Event, *, ref: str | None) -> TimelineState:
    if not ref:
        return state
    status = _status_of(event)
    kind = "failure" if status == "failed" else "task"
    for i, row in enumerate(state.rows):
        if row.kind in ("task", "failure") and row.ref == ref:
            updated = replace(
                row, kind=kind, glyph=_glyph_for(status), label=status, status=status
            )
            return replace(state, rows=(*state.rows[:i], updated, *state.rows[i + 1 :]))
    return _append(
        state,
        TimelineRow(
            order=len(state.rows),
            kind=kind,
            glyph=_glyph_for(status),
            label=status,
            text=_title_of(event, fallback=ref),
            status=status,
            ref=ref,
        ),
    )


def _reduce_message(state: TimelineState, event: Event) -> TimelineState:
    text = event.payload.get("text")
    if not isinstance(text, str) or not text:
        text = event.summary or ""
    role = event.payload.get("role")
    label = role if isinstance(role, str) and role else "agent"
    if text.startswith("FAILED"):
        attached = _attach_failure_detail(state, text)
        if attached is not None:
            return attached
        return _append(  # no matching failure row: keep it, styled as a failure
            state,
            TimelineRow(
                order=len(state.rows),
                kind="failure",
                glyph="✗",
                label=label,
                text=text,
                status="failed",
                ref="",
            ),
        )
    glyph = "?" if event.type in ("question_requested", "approval_requested") else "›"
    return _append(
        state,
        TimelineRow(
            order=len(state.rows),
            kind="message",
            glyph=glyph,
            label=label,
            text=text,
            status="",
            ref="",
        ),
    )


def _attach_failure_detail(state: TimelineState, text: str) -> TimelineState | None:
    """Attach ``FAILED <ref>[: detail]`` to its failure row (latest first)."""
    for i in range(len(state.rows) - 1, -1, -1):
        row = state.rows[i]
        if row.kind == "failure" and row.ref and row.ref in text:
            _, _, detail = text.partition(":")
            addition = detail.strip() or text
            merged = f"{row.detail}\n{addition}" if row.detail else addition
            updated = replace(row, detail=merged)
            return replace(state, rows=(*state.rows[:i], updated, *state.rows[i + 1 :]))
    return None


def _reduce_milestone(state: TimelineState, event: Event) -> TimelineState:
    failed = event.type == "run_failed" or event.status == "failed"
    label = {
        "run_started": "run started",
        "run_completed": "run failed" if failed else "run completed",
        "run_failed": "run failed",
    }[event.type]
    text = event.summary or label
    return _append(
        state,
        TimelineRow(
            order=len(state.rows),
            kind="milestone",
            glyph="✗" if failed else "◆",
            label=label,
            text=text,
            status="failed" if failed else "",
            ref="",
        ),
    )


def run_timeline_view(slice_name: str = "timeline") -> Selector[TimelineFeedView]:
    """A memoized selector projecting the timeline slice for the console."""

    @selector
    def _run_timeline(snapshot: Snapshot) -> TimelineFeedView:
        state: TimelineState = snapshot.slice(slice_name)
        return TimelineFeedView(rows=state.rows)

    return _run_timeline
