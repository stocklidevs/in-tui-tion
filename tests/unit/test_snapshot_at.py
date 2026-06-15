"""Store.snapshot_at: reconstruct historical state by re-reducing a prefix."""

from __future__ import annotations

from datetime import UTC, datetime

from intui.events import Event, Scope
from intui.kit.state import taskboard_slice
from intui.state import Snapshot, Store, compose_reducers


def _event(eid: str, type_: str = "task_started", **scope: str) -> Event:
    return Event(
        version="1",
        event_id=eid,
        run_id="r1",
        timestamp=datetime(2026, 6, 14, tzinfo=UTC),
        type=type_,
        scope=Scope(**scope),
    )


def _ntasks(snap: Snapshot) -> int:
    return len(snap.slice("taskboard").tasks)


def test_snapshot_at_equals_prefix_reduction() -> None:
    store = Store(compose_reducers(taskboard=taskboard_slice()))
    for i in range(5):
        store.ingest(_event(f"e{i}", "task_started", task_id=f"t{i}"))
    # after k events, k tasks exist
    assert _ntasks(store.snapshot_at(0)) == 0
    assert _ntasks(store.snapshot_at(3)) == 3
    assert _ntasks(store.snapshot_at(5)) == 5


def test_snapshot_at_end_matches_live() -> None:
    store = Store(compose_reducers(taskboard=taskboard_slice()))
    for i in range(4):
        store.ingest(_event(f"e{i}", "task_started", task_id=f"t{i}"))
    end = store.snapshot_at(len(store.events))
    assert _ntasks(end) == _ntasks(store.snapshot)


def test_snapshot_at_clamps_out_of_range() -> None:
    store = Store(compose_reducers(taskboard=taskboard_slice()))
    store.ingest(_event("e0", "task_started", task_id="t0"))
    assert _ntasks(store.snapshot_at(-5)) == 0
    assert _ntasks(store.snapshot_at(99)) == 1


def test_snapshot_at_does_not_mutate_live() -> None:
    store = Store(compose_reducers(taskboard=taskboard_slice()))
    for i in range(3):
        store.ingest(_event(f"e{i}", "task_started", task_id=f"t{i}"))
    live_before = _ntasks(store.snapshot)
    store.snapshot_at(1)
    assert _ntasks(store.snapshot) == live_before == 3


def test_snapshot_at_mirrors_per_event_isolation() -> None:
    # A reducer that raises on a specific event: live skips it (isolation), and
    # reconstruction must skip it too (the event is still in the retained log).
    def reducer(state: int, event: Event) -> int:
        if event.type == "boom":
            raise ValueError("kaboom")
        return state + 1

    store = Store(compose_reducers(count=(reducer, 0)))
    store.ingest(_event("e1", "tick"))
    store.ingest(_event("e2", "boom"))  # reduction raises -> isolated live
    store.ingest(_event("e3", "tick"))
    # live: 2 ticks counted, boom skipped
    assert store.snapshot.slice("count") == 2
    # reconstruction skips boom the same way (no raise)
    assert store.snapshot_at(3).slice("count") == 2
    assert store.snapshot_at(2).slice("count") == 1  # after e1, e2(skipped)
