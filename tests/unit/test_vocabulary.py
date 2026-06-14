"""Canonical event vocabulary: registry = union, no drift from reducers."""

from datetime import UTC, datetime

from intui.events import Event, Scope
from intui.kit.state import (
    ARTIFACT_EVENT_TYPES,
    CONVERSATION_EVENT_TYPES,
    KNOWN_EVENT_TYPES,
    METRICS_EVENT_TYPES,
    MODE_EVENT_TYPES,
    RUN_STATUS_EVENT_TYPES,
    TASKBOARD_EVENT_TYPES,
    VIEW_EVENT_TYPES,
    WORKSPACE_EVENT_TYPES,
    artifacts_slice,
    conversation_slice,
    mode_slice,
    taskboard_slice,
    view_slice,
)
from intui.state import Store, compose_reducers

_MODULE_SETS = [
    TASKBOARD_EVENT_TYPES,
    ARTIFACT_EVENT_TYPES,
    CONVERSATION_EVENT_TYPES,
    MODE_EVENT_TYPES,
    VIEW_EVENT_TYPES,
    RUN_STATUS_EVENT_TYPES,
    WORKSPACE_EVENT_TYPES,
    METRICS_EVENT_TYPES,
]


def test_registry_is_union_of_module_sets() -> None:
    union: set[str] = set()
    for s in _MODULE_SETS:
        union |= set(s)
    assert set(KNOWN_EVENT_TYPES) == union


def test_module_sets_are_disjoint() -> None:
    # each event type is owned by exactly one bundled reducer
    seen: set[str] = set()
    for s in _MODULE_SETS:
        assert not (seen & set(s)), f"overlap: {seen & set(s)}"
        seen |= set(s)


def _event(type_: str) -> Event:
    return Event(
        version="1",
        event_id=f"e-{type_}",
        run_id="r1",
        timestamp=datetime(2026, 6, 13, tzinfo=UTC),
        type=type_,
        scope=Scope(task_id="t1", work_item_id="w1", lane_id="l1"),
        payload={
            "mode": "Build",
            "view": "diff",
            "role": "agent",
            "text": "hi",
            "name": "x",
            "title": "t",
            "metrics": [],
            "unified": "",
        },
    )


def test_no_stale_declarations_taskboard() -> None:
    # every declared taskboard type actually changes the taskboard slice
    for type_ in TASKBOARD_EVENT_TYPES:
        store = Store(compose_reducers(taskboard=taskboard_slice()))
        before = store.snapshot.slice("taskboard")
        store.ingest(_event(type_))
        assert store.snapshot.slice("taskboard") != before, type_


def test_no_stale_declarations_other_modules() -> None:
    checks = [
        ("artifacts", artifacts_slice(), ARTIFACT_EVENT_TYPES),
        ("conversation", conversation_slice(), CONVERSATION_EVENT_TYPES),
        ("modes", mode_slice(("Plan", "Build", "Inspect")), MODE_EVENT_TYPES),
        ("views", view_slice(("tasks", "diff")), VIEW_EVENT_TYPES),
    ]
    for name, sl, types in checks:
        for type_ in types:
            store = Store(compose_reducers(**{name: sl}))
            before = store.snapshot.slice(name)
            store.ingest(_event(type_))
            assert store.snapshot.slice(name) != before, f"{name}:{type_}"


def test_unknown_type_not_in_registry() -> None:
    assert "totally_made_up" not in KNOWN_EVENT_TYPES
