"""The run timeline feed: one CHRONOLOGICAL, glyph+label column from the stream.

Rows are reduced directly from the event stream (not stitched from other
slices), so the feed order is the arrival order — the run reads top-to-bottom
the way it happened. Failure detail messages attach to their failure row as a
callout instead of floating away as unrelated lines.
"""

from __future__ import annotations

from pathlib import Path

from intui.emit import run_recorder
from intui.events import read_recording
from intui.kit.state import run_timeline_view, timeline_slice
from intui.state import Store, compose_reducers


def _store_from(path: Path) -> Store:
    store = Store(compose_reducers(timeline=timeline_slice()))
    for event in read_recording(path):
        store.ingest(event)
    return store


def test_rows_interleave_in_arrival_order(tmp_path: Path) -> None:
    out = tmp_path / "run.jsonl"
    rec = run_recorder(out, run_id="t")
    rec.run_started(summary="demo run")
    rec.work_item_started("w1", task_id="m.py", title="test_one")
    rec.work_item_completed("w1", task_id="m.py", status="completed")
    rec.agent("halfway there")  # a message BETWEEN the two work items
    rec.work_item_started("w2", task_id="m.py", title="test_two")
    rec.work_item_completed("w2", task_id="m.py", status="completed")
    rec.run_completed(status="passed")
    rec.close()

    view = run_timeline_view()(_store_from(out).snapshot)
    texts = [r.text for r in view.rows]
    # chronology: run start, first item, the message, second item, run end
    assert texts.index("test_one") < texts.index("halfway there") < texts.index("test_two")
    assert [r.order for r in view.rows] == sorted(r.order for r in view.rows)
    # every row carries glyph AND label (Principle IV: never color alone)
    assert all(r.glyph and r.label for r in view.rows)


def test_work_item_is_one_row_updated_in_place(tmp_path: Path) -> None:
    out = tmp_path / "run.jsonl"
    rec = run_recorder(out, run_id="t")
    rec.work_item_started("w1", task_id="m.py", title="test_one")
    rec.work_item_completed("w1", task_id="m.py", status="failed")
    rec.close()

    view = run_timeline_view()(_store_from(out).snapshot)
    rows = [r for r in view.rows if r.text == "test_one"]
    assert len(rows) == 1  # started/completed collapse into one row
    assert rows[0].kind == "failure"
    assert rows[0].glyph == "✗"
    assert rows[0].label == "failed"


def test_failure_detail_attaches_to_the_failure_row(tmp_path: Path) -> None:
    out = tmp_path / "run.jsonl"
    rec = run_recorder(out, run_id="t")
    rec.work_item_started("m::test_bad", task_id="m.py", title="test_bad")
    rec.work_item_completed("m::test_bad", task_id="m.py", status="failed")
    rec.system("FAILED m::test_bad: assert 1 == 2")
    rec.close()

    view = run_timeline_view()(_store_from(out).snapshot)
    fails = [r for r in view.rows if r.kind == "failure"]
    assert len(fails) == 1
    assert "assert 1 == 2" in fails[0].detail  # attached as callout detail...
    assert all("assert 1 == 2" not in r.text for r in view.rows)  # ...not a stray row


def test_plain_messages_and_unmatched_failures_stay_rows(tmp_path: Path) -> None:
    out = tmp_path / "run.jsonl"
    rec = run_recorder(out, run_id="t")
    rec.user("hello")
    rec.system("FAILED something-we-never-saw: boom")  # no matching failure row
    rec.close()

    view = run_timeline_view()(_store_from(out).snapshot)
    assert any(r.text == "hello" and r.kind == "message" for r in view.rows)
    stray = [r for r in view.rows if "boom" in r.text]
    assert len(stray) == 1 and stray[0].kind == "failure"  # kept, styled as failure


def test_empty_stream_yields_empty_feed(tmp_path: Path) -> None:
    out = tmp_path / "run.jsonl"
    rec = run_recorder(out, run_id="t")
    rec.close()
    view = run_timeline_view()(_store_from(out).snapshot)
    assert view.rows == ()
