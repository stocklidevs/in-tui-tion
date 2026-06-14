"""Stream validator: envelope errors, unknown-type warnings, line numbers."""

import json

from intui.events import validate_event, validate_stream

GOOD = {
    "version": "1",
    "event_id": "e1",
    "run_id": "r1",
    "timestamp": "2026-06-13T10:00:00Z",
    "type": "task_started",
    "scope": {"task_id": "t1"},
}
KNOWN = {"task_started", "task_completed"}


def test_validate_event_clean() -> None:
    assert validate_event(GOOD, known_types=KNOWN) == []


def test_validate_event_missing_field() -> None:
    bad = {k: v for k, v in GOOD.items() if k != "run_id"}
    issues = validate_event(bad)
    assert any(i.severity == "error" and "run_id" in i.reason for i in issues)


def test_validate_event_bad_timestamp() -> None:
    bad = {**GOOD, "timestamp": "not-a-time"}
    issues = validate_event(bad)
    assert any(i.severity == "error" and "timestamp" in i.reason for i in issues)


def test_validate_event_unknown_version_is_error() -> None:
    bad = {**GOOD, "version": "99"}
    issues = validate_event(bad)
    assert any(i.severity == "error" and "version" in i.reason for i in issues)


def test_unknown_type_is_warning_not_error() -> None:
    odd = {**GOOD, "type": "custom_thing"}
    issues = validate_event(odd, known_types=KNOWN)
    assert any(i.severity == "warning" and "custom_thing" in i.reason for i in issues)
    assert all(i.severity != "error" for i in issues)


def test_unknown_type_no_warning_without_known_types() -> None:
    odd = {**GOOD, "type": "custom_thing"}
    assert validate_event(odd) == []  # no vocabulary supplied -> no warning


def test_validate_stream_line_numbers_and_blank_lines() -> None:
    lines = [
        json.dumps(GOOD),
        "",  # blank skipped
        "{not json",  # line 3 error
        json.dumps({**GOOD, "event_id": "e2", "run_id": ""}),  # line 4 envelope error
    ]
    issues = validate_stream(lines, known_types=KNOWN)
    by_line = {i.line: i for i in issues}
    assert 3 in by_line and by_line[3].severity == "error"
    assert 4 in by_line and by_line[4].severity == "error"
    assert 2 not in by_line  # blank skipped


def test_validate_stream_unwraps_record_types() -> None:
    # producer wraps events: {"type":"run_trace_event","event":{...envelope...}}
    wrapped = json.dumps({"type": "run_trace_event", "event": GOOD})
    other = json.dumps({"type": "summary", "totals": 1})  # ignored
    issues = validate_stream(
        [wrapped, other], known_types=KNOWN, event_record_types=("run_trace_event",)
    )
    assert issues == []


def test_validate_stream_accepts_path(tmp_path) -> None:
    p = tmp_path / "s.jsonl"
    p.write_text(json.dumps(GOOD) + "\n", encoding="utf-8")
    assert validate_stream(p, known_types=KNOWN) == []
