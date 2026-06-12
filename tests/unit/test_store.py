"""Store: ingest -> reduce -> publish, dedupe, reducer-failure isolation (FR-008)."""

from datetime import UTC, datetime

from intui.events import Event, Scope, StreamState
from intui.state import Snapshot, Store, compose_reducers


def make_event(event_id: str, type_: str = "item_added", **payload: object) -> Event:
    return Event(
        version="1",
        event_id=event_id,
        run_id="run-1",
        timestamp=datetime(2026, 6, 12, tzinfo=UTC),
        type=type_,
        scope=Scope(),
        payload=payload,
    )


def items_reducer(items: tuple[str, ...], event: Event) -> tuple[str, ...]:
    if event.type == "item_added":
        return (*items, str(event.payload["name"]))
    if event.type == "explode":
        raise RuntimeError("boom")
    return items


def make_store() -> Store:
    return Store(compose_reducers(items=(items_reducer, ())))


def test_ingest_reduces_and_updates_snapshot() -> None:
    store = make_store()
    store.ingest(make_event("e1", name="alpha"))
    assert store.snapshot.slice("items") == ("alpha",)
    assert store.snapshot.state_version == 1


def test_ingest_publishes_to_subscribers() -> None:
    store = make_store()
    seen: list[Snapshot] = []
    store.subscribe(seen.append)
    store.ingest(make_event("e1", name="alpha"))
    assert len(seen) == 1
    assert seen[0].slice("items") == ("alpha",)


def test_unsubscribe_stops_notifications() -> None:
    store = make_store()
    seen: list[Snapshot] = []
    unsubscribe = store.subscribe(seen.append)
    unsubscribe()
    store.ingest(make_event("e1", name="alpha"))
    assert seen == []


def test_duplicate_event_id_not_rereduced() -> None:
    store = make_store()
    store.ingest(make_event("e1", name="alpha"))
    store.ingest(make_event("e1", name="beta"))  # duplicate id, dropped
    assert store.snapshot.slice("items") == ("alpha",)
    assert store.snapshot.state_version == 1


def test_reducer_exception_isolated_prior_snapshot_retained() -> None:
    store = make_store()
    store.ingest(make_event("e1", name="alpha"))
    before_items = store.snapshot.slice("items")
    store.ingest(make_event("e2", type_="explode"))
    after = store.snapshot
    assert after.slice("items") == before_items
    assert after.health.state is StreamState.ERRORING
    assert after.health.last_error is not None
    assert after.health.last_error.event_id == "e2"
    assert "boom" in after.health.last_error.reason


def test_recovery_after_reducer_failure() -> None:
    store = make_store()
    store.ingest(make_event("e1", type_="explode"))
    store.ingest(make_event("e2", name="alpha"))
    assert store.snapshot.slice("items") == ("alpha",)
    assert store.snapshot.health.state is StreamState.LIVE


def test_snapshot_health_reflects_stream() -> None:
    store = make_store()
    assert store.snapshot.health.state is StreamState.LIVE
    store.ingest(make_event("e1", name="alpha"))
    assert store.snapshot.health.last_event_at is not None
