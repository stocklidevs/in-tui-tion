"""Selectors: memoization per state_version, value equality, built-in health view."""

from datetime import UTC, datetime

from intui.events import Event, Scope, StreamState
from intui.state import Snapshot, Store, compose_reducers
from intui.viewmodels import health_view, selector


def make_event(event_id: str, **payload: object) -> Event:
    return Event(
        version="1",
        event_id=event_id,
        run_id="run-1",
        timestamp=datetime(2026, 6, 12, tzinfo=UTC),
        type="item_added",
        scope=Scope(),
        payload=payload,
    )


def items_reducer(items: tuple[str, ...], event: Event) -> tuple[str, ...]:
    if event.type == "item_added":
        return (*items, str(event.payload["name"]))
    return items


def test_selector_projects_snapshot() -> None:
    @selector
    def item_count(snapshot: Snapshot) -> str:
        return f"{len(snapshot.slice('items'))} items"

    store = Store(compose_reducers(items=(items_reducer, ())))
    store.ingest(make_event("e1", name="a"))
    assert item_count(store.snapshot) == "1 items"


def test_selector_memoizes_per_state_version() -> None:
    calls = []

    @selector
    def item_count(snapshot: Snapshot) -> int:
        calls.append(snapshot.state_version)
        return len(snapshot.slice("items"))

    store = Store(compose_reducers(items=(items_reducer, ())))
    store.ingest(make_event("e1", name="a"))
    snap = store.snapshot
    assert item_count(snap) == 1
    assert item_count(snap) == 1
    assert calls == [1]  # computed once for the same state_version


def test_selector_recomputes_on_new_version() -> None:
    calls = []

    @selector
    def item_count(snapshot: Snapshot) -> int:
        calls.append(snapshot.state_version)
        return len(snapshot.slice("items"))

    store = Store(compose_reducers(items=(items_reducer, ())))
    store.ingest(make_event("e1", name="a"))
    item_count(store.snapshot)
    store.ingest(make_event("e2", name="b"))
    assert item_count(store.snapshot) == 2
    assert calls == [1, 2]


def test_view_models_support_value_equality() -> None:
    @selector
    def items_vm(snapshot: Snapshot) -> tuple[str, ...]:
        return snapshot.slice("items")

    store = Store(compose_reducers(items=(items_reducer, ())))
    store.ingest(make_event("e1", name="a"))
    a = items_vm(store.snapshot)
    b = items_vm(store.snapshot)
    assert a == b


def test_health_view_reports_stream_state() -> None:
    store = Store(compose_reducers(items=(items_reducer, ())))
    view = health_view(store.snapshot)
    assert view.state is StreamState.LIVE
    assert view.rejected_count == 0
    assert isinstance(view.label, str) and view.label
