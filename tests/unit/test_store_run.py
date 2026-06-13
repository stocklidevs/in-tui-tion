"""Store.run: drive a source to completion; failures never raise (FR-008)."""

from collections.abc import AsyncIterator, Mapping
from typing import Any

from intui.events import Event, MemorySource, StreamState
from intui.state import Store, compose_reducers


def items_reducer(items: tuple[str, ...], event: Event) -> tuple[str, ...]:
    if event.type == "item_added":
        return (*items, str(event.payload["name"]))
    return items


def raw(event_id: str, **payload: object) -> dict[str, Any]:
    return {
        "version": "1",
        "event_id": event_id,
        "run_id": "run-1",
        "timestamp": "2026-06-12T12:00:00Z",
        "type": "item_added",
        "scope": {},
        "payload": payload,
    }


def make_store() -> Store:
    return Store(compose_reducers(items=(items_reducer, ())))


async def test_run_ends_with_ended_health() -> None:
    store = make_store()
    health = await store.run(MemorySource([raw("e1", name="a"), raw("e2", name="b")]))
    assert health.state is StreamState.ENDED
    assert store.snapshot.slice("items") == ("a", "b")


async def test_run_isolates_invalid_envelopes() -> None:
    store = make_store()
    bad = {"version": "99", "event_id": "bad"}
    health = await store.run(MemorySource([raw("e1", name="a"), bad, raw("e2", name="b")]))
    assert health.state is StreamState.ENDED  # rejected event did not stop the run
    assert health.rejected_count == 1
    assert store.snapshot.slice("items") == ("a", "b")


async def test_run_marks_disconnected_when_source_raises() -> None:
    class BrokenSource:
        async def __aiter__(self) -> AsyncIterator[Mapping[str, Any]]:
            yield raw("e1", name="a")
            raise ConnectionError("pipe lost")

    store = make_store()
    health = await store.run(BrokenSource())
    assert health.state is StreamState.DISCONNECTED
    assert store.snapshot.slice("items") == ("a",)
