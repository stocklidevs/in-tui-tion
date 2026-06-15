"""Store.events: the accepted-event history used to record a run."""

from __future__ import annotations

from datetime import UTC, datetime

from intui.events import Event, Scope
from intui.kit.state import taskboard_slice
from intui.state import Store, compose_reducers


def _event(eid: str, type_: str = "task_started", **scope: str) -> Event:
    return Event(
        version="1",
        event_id=eid,
        run_id="r1",
        timestamp=datetime(2026, 6, 14, tzinfo=UTC),
        type=type_,
        scope=Scope(**scope),
    )


def test_events_returns_accepted_in_order() -> None:
    store = Store(compose_reducers(taskboard=taskboard_slice()))
    store.ingest(_event("e1", task_id="t1"))
    store.ingest(_event("e2", task_id="t2"))
    assert [e.event_id for e in store.events] == ["e1", "e2"]
    assert isinstance(store.events, tuple)


def test_events_excludes_duplicates() -> None:
    store = Store(compose_reducers(taskboard=taskboard_slice()))
    store.ingest(_event("e1", task_id="t1"))
    store.ingest(_event("e1", task_id="t1"))  # duplicate id -> dropped
    assert [e.event_id for e in store.events] == ["e1"]


def test_events_excludes_malformed_raw() -> None:
    store = Store(compose_reducers(taskboard=taskboard_slice()))
    store.ingest_raw({"__malformed__": "bad", "line_number": 1})  # rejected
    store.ingest(_event("e1", task_id="t1"))
    assert [e.event_id for e in store.events] == ["e1"]
