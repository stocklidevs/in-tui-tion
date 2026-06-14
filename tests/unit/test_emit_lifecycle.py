"""Producer SDK: context managers emit started/completed pairs (+ failed)."""

from __future__ import annotations

from typing import Any

import pytest

from intui import run_recorder
from intui.events import read_recording
from intui.kit.state import taskboard_slice, tree_view
from intui.state import Store, compose_reducers


def _capture() -> tuple[list[dict[str, Any]], Any]:
    events: list[dict[str, Any]] = []
    return events, events.append


def _types(events: list[dict[str, Any]]) -> list[str]:
    return [e["type"] for e in events]


def test_run_context_brackets_with_lifecycle() -> None:
    events, sink = _capture()
    rec = run_recorder(sink, run_id="r1")
    with rec.run():
        rec.agent("working")
    assert _types(events) == ["run_started", "message_added", "run_completed"]


def test_run_context_marks_failed_on_exception() -> None:
    events, sink = _capture()
    rec = run_recorder(sink, run_id="r1")
    with pytest.raises(ValueError), rec.run():
        raise ValueError("boom")
    assert _types(events) == ["run_started", "run_failed"]


def test_task_context_emits_started_then_completed() -> None:
    events, sink = _capture()
    rec = run_recorder(sink, run_id="r1")
    with rec.task("build", "Build"):
        pass
    assert _types(events) == ["task_started", "task_completed"]
    assert events[-1].get("status") in (None, "passed", "completed")


def test_task_context_failed_on_exception_and_reraises() -> None:
    events, sink = _capture()
    rec = run_recorder(sink, run_id="r1")
    with pytest.raises(RuntimeError), rec.task("build", "Build"):
        raise RuntimeError("nope")
    assert _types(events) == ["task_started", "task_completed"]
    assert events[-1]["status"] == "failed"


def test_work_item_context_scoped_to_task_and_nests() -> None:
    events, sink = _capture()
    rec = run_recorder(sink, run_id="r1")
    with rec.task("build", "Build") as build, build.work_item("compile", title="compile"):
        pass
    assert _types(events) == [
        "task_started",
        "work_item_started",
        "work_item_completed",
        "task_completed",
    ]
    wi = events[1]
    assert wi["scope"]["task_id"] == "build" and wi["scope"]["work_item_id"] == "compile"


def test_work_item_nests_under_task_when_reduced() -> None:
    events, sink = _capture()
    rec = run_recorder(sink, run_id="r1")
    with rec.task("build", "Build") as build, build.work_item("compile", title="compile"):
        pass
    store = Store(compose_reducers(taskboard=taskboard_slice()))
    from intui.events import parse_event

    for env in events:
        store.ingest(parse_event(env))
    build_row = next(t for t in tree_view()(store.snapshot).tasks if t.title == "Build")
    assert [i.title for i in build_row.items] == ["compile"]


def test_lifecycle_round_trips_to_file(tmp_path: Any) -> None:
    path = tmp_path / "run.ndjson"
    with run_recorder(path, run_id="r1") as rec, rec.run():  # noqa: SIM117
        with rec.task("build", "Build") as build, build.work_item("compile"):
            pass
    types = [e.type for e in read_recording(path)]
    assert types == [
        "run_started",
        "task_started",
        "work_item_started",
        "work_item_completed",
        "task_completed",
        "run_completed",
    ]
