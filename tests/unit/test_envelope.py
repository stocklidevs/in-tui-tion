"""Envelope contract tests (contracts/event-envelope.schema.json, schema v1)."""

import dataclasses
from datetime import UTC, datetime

import pytest

from intui.events import EnvelopeError, Event, Scope, parse_event


def make_raw(**overrides: object) -> dict[str, object]:
    raw: dict[str, object] = {
        "version": "1",
        "event_id": "evt-001",
        "run_id": "run-123",
        "timestamp": "2026-06-12T12:00:00Z",
        "type": "task_started",
        "scope": {"session_id": "session-abc", "task_id": "task-plan"},
        "status": "running",
        "summary": "Checking API shape",
        "payload": {"key": "value"},
    }
    raw.update(overrides)
    return raw


def test_parse_event_happy_path() -> None:
    event = parse_event(make_raw())
    assert event.version == "1"
    assert event.event_id == "evt-001"
    assert event.run_id == "run-123"
    assert event.timestamp == datetime(2026, 6, 12, 12, 0, 0, tzinfo=UTC)
    assert event.type == "task_started"
    assert event.scope.session_id == "session-abc"
    assert event.scope.task_id == "task-plan"
    assert event.status == "running"
    assert event.summary == "Checking API shape"
    assert event.payload == {"key": "value"}


def test_optional_fields_default() -> None:
    raw = make_raw()
    del raw["status"], raw["summary"], raw["payload"]
    event = parse_event(raw)
    assert event.status is None
    assert event.summary is None
    assert event.payload == {}


@pytest.mark.parametrize("field", ["version", "event_id", "run_id", "timestamp", "type", "scope"])
def test_missing_required_field_rejected(field: str) -> None:
    raw = make_raw()
    del raw[field]
    with pytest.raises(EnvelopeError, match=field):
        parse_event(raw)


@pytest.mark.parametrize("field", ["event_id", "run_id", "type"])
def test_empty_required_string_rejected(field: str) -> None:
    with pytest.raises(EnvelopeError, match=field):
        parse_event(make_raw(**{field: ""}))


def test_unknown_envelope_version_rejected() -> None:
    with pytest.raises(EnvelopeError, match="version"):
        parse_event(make_raw(version="99"))


def test_unparseable_timestamp_rejected() -> None:
    with pytest.raises(EnvelopeError, match="timestamp"):
        parse_event(make_raw(timestamp="not-a-time"))


def test_unknown_event_type_accepted() -> None:
    event = parse_event(make_raw(type="totally_custom_event"))
    assert event.type == "totally_custom_event"


def test_adapter_specific_scope_keys_preserved() -> None:
    event = parse_event(make_raw(scope={"task_id": "t1", "custom_key": "custom"}))
    assert event.scope.task_id == "t1"
    assert event.scope.extra == {"custom_key": "custom"}


def test_envelope_error_carries_event_id_when_known() -> None:
    with pytest.raises(EnvelopeError) as excinfo:
        parse_event(make_raw(timestamp="bad"))
    assert excinfo.value.event_id == "evt-001"


def test_event_is_frozen() -> None:
    event = parse_event(make_raw())
    with pytest.raises(dataclasses.FrozenInstanceError):
        event.type = "mutated"  # type: ignore[misc]


def test_public_safe_payload_metadata_preserved_untouched() -> None:
    event = parse_event(make_raw(payload={"public_safe": False, "secret_path": "C:/x"}))
    assert event.payload["public_safe"] is False
    assert event.payload["secret_path"] == "C:/x"


def test_scope_constructible_directly() -> None:
    scope = Scope(task_id="t1")
    assert scope.session_id is None
    assert scope.task_id == "t1"


def test_event_constructible_directly() -> None:
    event = Event(
        version="1",
        event_id="e1",
        run_id="r1",
        timestamp=datetime(2026, 6, 12, tzinfo=UTC),
        type="x",
        scope=Scope(),
    )
    assert event.payload == {}
