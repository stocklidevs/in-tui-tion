"""Producer SDK: run_recorder emits valid canonical envelopes, easily."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from intui import run_recorder
from intui.events import read_recording, validate_event
from intui.kit.state import (
    KNOWN_EVENT_TYPES,
    artifacts_slice,
    diff_view,
    evidence_view,
    taskboard_slice,
    tree_view,
)
from intui.state import Store, compose_reducers


def _capture() -> tuple[list[dict[str, Any]], Any]:
    events: list[dict[str, Any]] = []
    return events, events.append


def _fixed_clock() -> datetime:
    return datetime(2026, 6, 14, 12, 0, 0, tzinfo=UTC)


def test_emit_builds_a_valid_canonical_envelope() -> None:
    events, sink = _capture()
    rec = run_recorder(sink, run_id="r1", clock=_fixed_clock)
    ev = rec.task_started("build", title="Build")
    assert ev.type == "task_started" and ev.scope.task_id == "build"
    assert events[0]["type"] == "task_started"
    assert events[0]["version"] == "1" and events[0]["run_id"] == "r1"
    assert events[0]["payload"]["name"] == "Build"


def test_all_helpers_emit_known_vocabulary() -> None:
    events, sink = _capture()
    rec = run_recorder(sink, run_id="r1")
    rec.task_created("t")
    rec.task_started("t")
    rec.task_blocked("t")
    rec.task_completed("t", status="passed")
    rec.work_item_started("w", task_id="t")
    rec.work_item_completed("w", task_id="t")
    rec.subagent_started("l", name="verifier")
    rec.subagent_activity("l", summary="checking")
    rec.subagent_completed("l", status="passed")
    rec.agent("hi")
    rec.user("hello")
    rec.system("note")
    rec.question("which?")
    rec.approval("ok?")
    rec.view("diff")
    rec.mode("Build")
    rec.activity("thinking")
    rec.run_started()
    rec.run_completed()
    for env in events:
        issues = validate_event(env, known_types=KNOWN_EVENT_TYPES)
        assert [i for i in issues if i.severity == "error"] == [], env["type"]
    # lifecycle/activity types are part of the known vocabulary (no warnings)
    warn = [i for env in events for i in validate_event(env, known_types=KNOWN_EVENT_TYPES)]
    assert all(i.severity != "error" for i in warn)


def test_event_ids_unique_and_ordered() -> None:
    events, sink = _capture()
    rec = run_recorder(sink, run_id="r1")
    for i in range(3):
        rec.agent(f"m{i}")
    ids = [e["event_id"] for e in events]
    assert ids == ["e1", "e2", "e3"]


def test_generic_emit_supports_custom_type() -> None:
    events, sink = _capture()
    rec = run_recorder(sink, run_id="r1")
    ev = rec.emit("custom_thing", task_id="t", foo="bar")
    assert ev.type == "custom_thing"
    assert events[0]["scope"]["task_id"] == "t"
    assert events[0]["payload"]["foo"] == "bar"
    # custom type is a valid envelope (open vocabulary), only a warning vs known
    issues = validate_event(events[0], known_types=KNOWN_EVENT_TYPES)
    assert all(i.severity != "error" for i in issues)


def test_file_sink_writes_ndjson_and_round_trips(tmp_path: Path) -> None:
    path = tmp_path / "run.ndjson"
    with run_recorder(path, run_id="r1") as rec:
        rec.task_started("build", title="Build")
        rec.task_completed("build", status="passed")
    lines = [ln for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]
    assert len(lines) == 2
    assert json.loads(lines[0])["type"] == "task_started"
    events = read_recording(path)  # parses cleanly -> valid envelopes
    assert [e.type for e in events] == ["task_started", "task_completed"]


def test_recording_reduces_through_the_kit(tmp_path: Path) -> None:
    path = tmp_path / "run.ndjson"
    with run_recorder(path, run_id="r1") as rec:
        rec.task_started("build", title="Build")
        rec.work_item_started("compile", task_id="build", title="compile")
        rec.work_item_completed("compile", task_id="build", status="passed")
    store = Store(compose_reducers(taskboard=taskboard_slice()))
    for ev in read_recording(path):
        store.ingest(ev)
    tree = tree_view()(store.snapshot)
    build = next(t for t in tree.tasks if t.title == "Build")
    assert [i.title for i in build.items] == ["compile"]


def test_default_sink_is_stdout(capsys: Any) -> None:
    rec = run_recorder(run_id="r1")
    rec.agent("hello")
    out = capsys.readouterr().out
    assert json.loads(out.strip())["payload"]["text"] == "hello"


# --- diff / evidence ---------------------------------------------------------


def _store_artifacts(events: list[dict[str, Any]]) -> Store:
    from intui.events import parse_event

    store = Store(compose_reducers(artifacts=artifacts_slice()))
    for env in events:
        store.ingest(parse_event(env))
    return store


def test_diff_builds_unified_and_parses_into_files() -> None:
    events, sink = _capture()
    rec = run_recorder(sink, run_id="r1")
    rec.diff("src/app.py", before="old line\n", after="new line\n")
    assert events[0]["type"] == "diff_ready"
    view = diff_view()(_store_artifacts(events).snapshot)
    assert [f.path for f in view.files] == ["src/app.py"]
    body = "".join(line.text for line in view.body("src/app.py"))
    assert "new line" in body and "old line" in body


def test_multiple_diffs_accumulate() -> None:
    events, sink = _capture()
    rec = run_recorder(sink, run_id="r1")
    rec.diff("a.py", before="1\n", after="2\n")
    rec.diff("b.py", before="3\n", after="4\n")
    view = diff_view()(_store_artifacts(events).snapshot)
    assert {f.path for f in view.files} == {"a.py", "b.py"}


def test_diff_identical_before_after_no_crash() -> None:
    events, sink = _capture()
    rec = run_recorder(sink, run_id="r1")
    ev = rec.diff("same.py", before="x\n", after="x\n")
    assert ev.type == "diff_ready"  # emitted, empty diff, no error


def test_diff_unified_passthrough() -> None:
    events, sink = _capture()
    rec = run_recorder(sink, run_id="r1")
    unified = "--- a/x.py\n+++ b/x.py\n@@ -1 +1 @@\n-a\n+b\n"
    rec.diff_unified(unified, title="change")
    view = diff_view()(_store_artifacts(events).snapshot)
    assert [f.path for f in view.files] == ["x.py"]


def test_evidence_emits_metrics() -> None:
    events, sink = _capture()
    rec = run_recorder(sink, run_id="r1")
    rec.evidence(pass_rate="92%", certified="gold")
    assert events[0]["type"] == "evidence_ready"
    rows = evidence_view()(_store_artifacts(events).snapshot).rows
    keys = {r.key for r in rows}
    assert {"pass_rate", "certified"} <= keys


def test_metric_sample_helper() -> None:
    from intui.events import parse_event
    from intui.kit.state import metrics_slice

    events, sink = _capture()
    rec = run_recorder(sink, run_id="r1")
    rec.metric_sample(cpu_percent=42.0, rss_bytes=53_400_000, elapsed_ms=1200)
    assert events[0]["type"] == "metric_sample"
    store = Store(compose_reducers(metrics=metrics_slice()))
    for env in events:
        store.ingest(parse_event(env))
    m = store.snapshot.slice("metrics")
    assert m.cpu_percent == 42.0 and m.rss_bytes == 53_400_000


def test_file_helpers_build_the_tree() -> None:
    from intui.events import parse_event
    from intui.kit.state import file_tree_view, workspace_slice

    events, sink = _capture()
    rec = run_recorder(sink, run_id="r1")
    rec.file_written("src/app.py", change_type="added")
    rec.file_written("README.md")
    rec.file_removed("src/old.py")
    assert events[0]["type"] == "file_written" and events[0]["payload"]["path"] == "src/app.py"
    store = Store(compose_reducers(workspace=workspace_slice()))
    for env in events:
        store.ingest(parse_event(env))
    roots = file_tree_view()(store.snapshot).roots
    assert {n.name for n in roots} == {"src", "README.md"}
