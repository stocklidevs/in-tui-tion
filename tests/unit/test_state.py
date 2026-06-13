"""Snapshot and reducer semantics (FR-003, data-model.md)."""

from datetime import UTC, datetime

from intui.events import Event, Scope
from intui.state import compose_reducers


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
    return items


def counter_reducer(count: int, event: Event) -> int:
    if event.type == "item_added":
        return count + 1
    return count


def test_initial_snapshot_has_version_zero_and_slices() -> None:
    reducer = compose_reducers(items=(items_reducer, ()), count=(counter_reducer, 0))
    snapshot = reducer.initial()
    assert snapshot.state_version == 0
    assert snapshot.slice("items") == ()
    assert snapshot.slice("count") == 0


def test_reduction_updates_owning_slices() -> None:
    reducer = compose_reducers(items=(items_reducer, ()), count=(counter_reducer, 0))
    snapshot = reducer.initial()
    snapshot = reducer(snapshot, make_event("e1", name="alpha"))
    assert snapshot.slice("items") == ("alpha",)
    assert snapshot.slice("count") == 1


def test_state_version_is_monotonic_per_event() -> None:
    reducer = compose_reducers(items=(items_reducer, ()))
    snapshot = reducer.initial()
    for i in range(3):
        snapshot = reducer(snapshot, make_event(f"e{i}", name=f"n{i}"))
    assert snapshot.state_version == 3


def test_unknown_event_type_passes_through_unchanged() -> None:
    reducer = compose_reducers(items=(items_reducer, ()))
    snapshot = reducer.initial()
    before = snapshot
    snapshot = reducer(snapshot, make_event("e1", type_="totally_unknown"))
    assert snapshot.slice("items") == before.slice("items")


def test_deterministic_reduction_same_sequence_equal_snapshots() -> None:
    events = [make_event(f"e{i}", name=f"n{i}") for i in range(5)]
    reducer = compose_reducers(items=(items_reducer, ()), count=(counter_reducer, 0))
    run1 = reducer.initial()
    run2 = reducer.initial()
    for event in events:
        run1 = reducer(run1, event)
    for event in events:
        run2 = reducer(run2, event)
    assert run1 == run2  # structural equality (SC-002)


def test_snapshots_with_different_history_are_unequal() -> None:
    reducer = compose_reducers(count=(counter_reducer, 0))
    base = reducer.initial()
    one = reducer(base, make_event("e1"))
    assert base != one


def test_snapshot_is_immutable() -> None:
    reducer = compose_reducers(count=(counter_reducer, 0))
    snapshot = reducer.initial()
    try:
        snapshot.state_version = 99  # type: ignore[misc]
        raised = False
    except (AttributeError, TypeError):
        raised = True
    assert raised


def test_unknown_slice_name_raises_key_error() -> None:
    reducer = compose_reducers(count=(counter_reducer, 0))
    snapshot = reducer.initial()
    try:
        snapshot.slice("nope")
        raised = False
    except KeyError:
        raised = True
    assert raised
