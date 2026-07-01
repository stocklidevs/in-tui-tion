"""The run timeline feed: one ordered, glyph+label column from the slices."""

from __future__ import annotations

from pathlib import Path

from intui.emit import run_recorder
from intui.events import read_recording
from intui.kit.state import (
    conversation_slice,
    run_status_slice,
    run_timeline_view,
    taskboard_slice,
)
from intui.state import Store, compose_reducers


def _store_from(path: Path) -> Store:
    store = Store(
        compose_reducers(
            taskboard=taskboard_slice(),
            conversation=conversation_slice(),
            run_status=run_status_slice(),
        )
    )
    for event in read_recording(path):
        store.ingest(event)
    return store


def _record_run(path: Path) -> None:
    rec = run_recorder(path, run_id="t")
    rec.run_started(summary="pytest run")
    rec.work_item_started("m::test_ok", task_id="m.py", title="test_ok")
    rec.work_item_completed("m::test_ok", task_id="m.py", status="completed")
    rec.work_item_started("m::test_bad", task_id="m.py", title="test_bad")
    rec.work_item_completed("m::test_bad", task_id="m.py", status="failed")
    rec.system("FAILED m::test_bad: assert 1 == 2")
    rec.run_failed()
    rec.close()


def test_rows_are_ordered_and_carry_glyph_and_label(tmp_path: Path) -> None:
    out = tmp_path / "run.jsonl"
    _record_run(out)

    store = _store_from(out)
    view = run_timeline_view()(store.snapshot)

    assert view.rows
    assert [r.order for r in view.rows] == sorted(r.order for r in view.rows)
    # every row has a non-empty glyph AND label (Principle IV: never color alone)
    assert all(r.glyph and r.label for r in view.rows)
    # the failed work item surfaces as a failure row
    fails = [r for r in view.rows if r.kind == "failure"]
    assert any("test_bad" in r.text for r in fails)
    assert all(r.glyph == "✗" for r in fails)


def test_empty_snapshot_yields_empty_feed(tmp_path: Path) -> None:
    out = tmp_path / "run.jsonl"
    rec = run_recorder(out, run_id="t")
    rec.close()
    store = _store_from(out)
    view = run_timeline_view()(store.snapshot)
    assert view.rows == ()
