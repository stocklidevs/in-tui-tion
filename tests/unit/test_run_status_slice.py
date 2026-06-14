"""run_status_slice: lifecycle/synthetic events -> KITT activity states."""

from __future__ import annotations

from datetime import UTC, datetime

from intui.events import Event, Scope
from intui.kit.state import (
    ACTIVITY_STATES,
    KNOWN_EVENT_TYPES,
    RUN_STATUS_EVENT_TYPES,
    run_status_slice,
)


def _event(type_: str, **payload: object) -> Event:
    return Event(
        version="1",
        event_id=f"{type_}-1",
        run_id="r1",
        timestamp=datetime.now(tz=UTC),
        type=type_,
        scope=Scope(),
        payload=payload,
    )


def test_initial_state_is_idle() -> None:
    _reducer, initial = run_status_slice()
    assert initial == "idle"


def test_lifecycle_maps_to_activity_states() -> None:
    reducer, initial = run_status_slice()
    cases = {
        "run_started": "thinking",
        "task_started": "thinking",
        "subagent_started": "thinking",
        "task_blocked": "waiting",
        "gate_started": "verifying",
        "run_failed": "failure",
        "run_completed": "passed",
    }
    for type_, expected in cases.items():
        assert reducer(initial, _event(type_)) == expected
        assert expected in ACTIVITY_STATES


def test_activity_set_carries_explicit_state() -> None:
    reducer, initial = run_status_slice()
    assert reducer(initial, _event("activity_set", state="verifying")) == "verifying"


def test_unknown_type_passes_through() -> None:
    reducer, _initial = run_status_slice()
    assert reducer("thinking", _event("some_other_event")) == "thinking"


def test_event_types_are_in_known_vocabulary() -> None:
    assert RUN_STATUS_EVENT_TYPES <= KNOWN_EVENT_TYPES
