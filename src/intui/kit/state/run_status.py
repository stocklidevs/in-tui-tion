"""Run-status reducer: map the run lifecycle to a KITT activity state (R6).

Engine-free. The overall run state is a single string drawn from
``ACTIVITY_STATES`` (see :mod:`intui.kit.state.activity`); the ``ActivityStrip``
renders it. Kept here as a first-class slice so the batteries-included console
needs no application reducers and the activity lifecycle vocabulary is part of
the canonical contract (``RUN_STATUS_EVENT_TYPES`` unions into
``KNOWN_EVENT_TYPES``).
"""

from __future__ import annotations

from typing import Any

from intui.events.envelope import Event

#: Lifecycle/synthetic types this reducer *introduces* to the vocabulary.
#: The reducer also reacts to ``task_started``/``task_blocked`` (owned by the
#: taskboard reducer) and ``subagent_started`` (owned by the conversation
#: reducer) — those stay owned by exactly one module while still mapping to an
#: activity state here.
RUN_STATUS_EVENT_TYPES: frozenset[str] = frozenset(
    {
        "activity_set",
        "run_started",
        "gate_started",
        "run_failed",
        "run_completed",
    }
)


def run_status_reducer(status: str, event: Event) -> str:
    """Map run + synthetic events to R6 activity states for the KITT strip.

    Unknown types pass the current status through unchanged (open vocabulary).
    """
    if event.type == "activity_set":
        return str(event.payload["state"])
    if event.type in {"run_started", "task_started", "subagent_started"}:
        return "thinking"
    if event.type == "task_blocked":
        return "waiting"
    if event.type == "gate_started":
        return "verifying"
    if event.type == "run_failed":
        return "failure"
    if event.type == "run_completed":
        return "passed"
    return status


def run_status_slice() -> tuple[Any, str]:
    """``(reducer, initial)`` pair for ``compose_reducers(run_status=...)``."""
    return run_status_reducer, "idle"
