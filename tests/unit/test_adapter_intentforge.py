"""adapt_record: IntentForge run-trace records -> canonical envelopes."""

from __future__ import annotations

from typing import Any

from intui.adapters import adapt_record
from intui.events import Event, validate_event
from intui.kit.state import KNOWN_EVENT_TYPES

UNIFIED = "--- a/app.py\n+++ b/app.py\n@@ -1,2 +1,2 @@\n-old line\n+new line\n context\n"


def _wrap(name: str, payload: dict[str, Any], *, sequence: int = 1) -> dict[str, Any]:
    return {
        "type": "run_trace_event",
        "event": {"sequence": sequence, "name": name, "payload": payload},
    }


def _bare(name: str, payload: dict[str, Any], *, sequence: int = 1) -> dict[str, Any]:
    return {"sequence": sequence, "name": name, "payload": payload}


def test_case_started_to_task_started() -> None:
    ev = adapt_record(_wrap("case_started", {"case_id": "c1", "index": 1, "total": 3}))
    assert ev is not None
    assert ev.type == "task_started"
    assert ev.scope.task_id == "c1"
    assert ev.version == "1" and ev.run_id == "intentforge"


def test_case_finished_failed_sets_status() -> None:
    ev = adapt_record(_wrap("case_finished", {"case_id": "c1", "status": "failed"}))
    assert ev is not None and ev.type == "task_completed"
    assert ev.scope.task_id == "c1"
    assert ev.status == "failed"


def test_assembly_item_uses_work_item_id_then_case_id() -> None:
    started = adapt_record(_wrap("assembly_item_started", {"case_id": "w1"}))
    assert started is not None and started.type == "work_item_started"
    assert started.scope.work_item_id == "w1"
    committed = adapt_record(
        _wrap("assembly_item_committed", {"case_id": "x", "work_item_id": "w2"})
    )
    assert committed is not None and committed.type == "work_item_completed"
    assert committed.scope.work_item_id == "w2"


def test_assembly_item_failed_status() -> None:
    ev = adapt_record(_wrap("assembly_item_failed", {"case_id": "w1", "status": "failed"}))
    assert ev is not None and ev.type == "work_item_completed"
    assert ev.status == "failed"


def test_assembly_plan_blocked_to_task_blocked() -> None:
    ev = adapt_record(_wrap("assembly_plan_blocked", {"case_id": "bp1", "status": "blocked"}))
    assert ev is not None and ev.type == "task_blocked"
    assert ev.scope.task_id == "bp1"


def test_matrix_lifecycle_to_run_lifecycle() -> None:
    started = adapt_record(_wrap("matrix_suite_started", {"suite_id": "s1"}))
    finished = adapt_record(_wrap("matrix_suite_finished", {"suite_id": "s1", "status": "passed"}))
    assert started is not None and started.type == "run_started"
    assert finished is not None and finished.type == "run_completed"


def test_file_diff_to_diff_ready_with_unified() -> None:
    ev = adapt_record(
        _wrap(
            "file_diff", {"case_id": "w1", "work_item_id": "w1", "diff": UNIFIED, "file": "app.py"}
        )
    )
    assert ev is not None and ev.type == "diff_ready"
    assert ev.payload["unified"] == UNIFIED
    assert ev.payload["public_safe"] is True


def test_file_diff_missing_diff_is_empty_not_crash() -> None:
    ev = adapt_record(_wrap("file_diff", {"case_id": "w1"}))
    assert ev is not None and ev.type == "diff_ready"
    assert ev.payload["unified"] == ""


def test_repeat_events_to_messages() -> None:
    started = adapt_record(_wrap("repeat_started", {"run_index": 1, "repeat_count": 3}))
    finished = adapt_record(
        _wrap("repeat_finished", {"run_index": 1, "repeat_count": 3, "status": "passed"})
    )
    assert started is not None and started.type == "message_added"
    assert started.payload["role"] == "system"
    assert finished is not None and "passed" in finished.payload["text"]


def test_summary_to_evidence_ready() -> None:
    record = {
        "type": "summary",
        "summary": {
            "case_pass_rate": 0.8,
            "quality_issue_count": 2,
            "acb_score": {"certified_level": "silver"},
            "ignored_nested": {"deep": 1},
        },
    }
    ev = adapt_record(record)
    assert ev is not None and ev.type == "evidence_ready"
    assert ev.event_id == "if-summary"
    keys = {m["key"] for m in ev.payload["metrics"]}
    assert "case_pass_rate" in keys and "quality_issue_count" in keys
    assert "certified_level" in keys  # lifted from acb_score


def test_unknown_name_returns_none() -> None:
    assert adapt_record(_wrap("totally_made_up", {"case_id": "c1"})) is None


def test_accepts_bare_inner_record() -> None:
    ev = adapt_record(_bare("case_started", {"case_id": "c1"}))
    assert ev is not None and ev.type == "task_started"


def test_event_id_and_timestamp_deterministic_from_sequence() -> None:
    a = adapt_record(_wrap("case_started", {"case_id": "c1"}, sequence=5))
    b = adapt_record(_wrap("case_started", {"case_id": "c1"}, sequence=5))
    assert a is not None and b is not None
    assert a.event_id == b.event_id == "if-5"
    assert a.timestamp == b.timestamp
    later = adapt_record(_wrap("case_started", {"case_id": "c2"}, sequence=6))
    assert later is not None and later.timestamp > a.timestamp


def test_adapter_output_validates_against_vocabulary() -> None:
    records = [
        _wrap("matrix_suite_started", {"suite_id": "s1"}, sequence=1),
        _wrap("case_started", {"case_id": "c1"}, sequence=2),
        _wrap("file_diff", {"case_id": "w1", "diff": UNIFIED}, sequence=3),
        _wrap("case_finished", {"case_id": "c1", "status": "passed"}, sequence=4),
        {"type": "summary", "summary": {"case_pass_rate": 1.0}},
    ]
    for rec in records:
        ev = adapt_record(rec)
        assert ev is not None
        issues = validate_event(ev.to_mapping(), known_types=KNOWN_EVENT_TYPES)
        assert [i for i in issues if i.severity == "error"] == []
        assert isinstance(ev, Event)
