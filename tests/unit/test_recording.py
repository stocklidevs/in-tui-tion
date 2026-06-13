"""Recording round-trip: JSONL write/read, malformed-line policy (FR-006)."""

from datetime import UTC, datetime
from pathlib import Path

import pytest

from intui.events import EnvelopeError, Event, Scope, read_recording, write_recording


def make_event(event_id: str, **payload: object) -> Event:
    return Event(
        version="1",
        event_id=event_id,
        run_id="run-1",
        timestamp=datetime(2026, 6, 12, 12, 0, tzinfo=UTC),
        type="item_added",
        scope=Scope(session_id="s1", extra={"custom": "x"}),
        status="running",
        summary="adding an item",
        payload=payload,
    )


def test_round_trip_is_lossless(tmp_path: Path) -> None:
    events = [make_event(f"e{i}", name=f"n{i}") for i in range(3)]
    path = tmp_path / "run.jsonl"
    write_recording(path, events)
    loaded = read_recording(path)
    assert loaded == events


def test_recording_is_one_json_object_per_line_utf8(tmp_path: Path) -> None:
    path = tmp_path / "run.jsonl"
    write_recording(path, [make_event("e1", emoji="✨")])
    lines = path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    assert '"event_id": "e1"' in lines[0] or '"event_id":"e1"' in lines[0]


def test_malformed_line_skipped_by_default(tmp_path: Path) -> None:
    path = tmp_path / "run.jsonl"
    write_recording(path, [make_event("e1"), make_event("e2")])
    content = path.read_text(encoding="utf-8").splitlines()
    content.insert(1, "{not valid json")
    path.write_text("\n".join(content) + "\n", encoding="utf-8")

    loaded = read_recording(path)  # on_malformed="skip"
    assert [e.event_id for e in loaded] == ["e1", "e2"]


def test_malformed_line_halts_with_line_number_when_requested(tmp_path: Path) -> None:
    path = tmp_path / "run.jsonl"
    write_recording(path, [make_event("e1")])
    with path.open("a", encoding="utf-8") as f:
        f.write("{not valid json\n")

    with pytest.raises(EnvelopeError) as excinfo:
        read_recording(path, on_malformed="halt")
    assert excinfo.value.line_number == 2


def test_invalid_envelope_line_reported_with_line_number(tmp_path: Path) -> None:
    path = tmp_path / "run.jsonl"
    write_recording(path, [make_event("e1")])
    with path.open("a", encoding="utf-8") as f:
        f.write('{"version": "99", "event_id": "bad"}\n')

    with pytest.raises(EnvelopeError) as excinfo:
        read_recording(path, on_malformed="halt")
    assert excinfo.value.line_number == 2
    assert "version" in excinfo.value.reason


def test_supported_version_envelope_accepted(tmp_path: Path) -> None:
    # Schema v1 is the oldest (and currently only) supported envelope version;
    # recordings written today must stay readable.
    path = tmp_path / "run.jsonl"
    write_recording(path, [make_event("e1")])
    loaded = read_recording(path)
    assert loaded[0].version == "1"


def test_blank_lines_ignored(tmp_path: Path) -> None:
    path = tmp_path / "run.jsonl"
    write_recording(path, [make_event("e1")])
    with path.open("a", encoding="utf-8") as f:
        f.write("\n\n")
    assert [e.event_id for e in read_recording(path)] == ["e1"]
