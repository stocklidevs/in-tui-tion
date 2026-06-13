"""EventStream semantics: append-only, dedupe, health transitions (data-model.md)."""

from datetime import UTC, datetime

from intui.events import Event, EventStream, Scope, StreamState


def make_event(event_id: str, type_: str = "task_started") -> Event:
    return Event(
        version="1",
        event_id=event_id,
        run_id="run-1",
        timestamp=datetime(2026, 6, 12, 12, 0, tzinfo=UTC),
        type=type_,
        scope=Scope(),
    )


def test_append_accepts_new_events_in_order() -> None:
    stream = EventStream()
    assert stream.append(make_event("e1"))
    assert stream.append(make_event("e2"))
    assert [e.event_id for e in stream.events] == ["e1", "e2"]


def test_duplicate_event_id_dropped_and_counted() -> None:
    stream = EventStream()
    assert stream.append(make_event("e1"))
    assert not stream.append(make_event("e1", type_="different_type"))
    assert [e.event_id for e in stream.events] == ["e1"]
    assert stream.health.duplicate_count == 1


def test_events_view_is_immutable() -> None:
    stream = EventStream()
    stream.append(make_event("e1"))
    events = stream.events
    assert not hasattr(events, "append") or not callable(getattr(events, "append", None))


def test_initial_health_is_live() -> None:
    assert EventStream().health.state is StreamState.LIVE


def test_health_tracks_last_event_at() -> None:
    stream = EventStream()
    event = make_event("e1")
    stream.append(event)
    assert stream.health.last_event_at == event.timestamp


def test_mark_ended() -> None:
    stream = EventStream()
    stream.mark_ended()
    assert stream.health.state is StreamState.ENDED


def test_mark_disconnected() -> None:
    stream = EventStream()
    stream.mark_disconnected()
    assert stream.health.state is StreamState.DISCONNECTED


def test_rejection_moves_to_erroring_and_records_error() -> None:
    stream = EventStream()
    stream.record_rejection("e9", "bad envelope")
    assert stream.health.state is StreamState.ERRORING
    assert stream.health.rejected_count == 1
    assert stream.health.last_error is not None
    assert stream.health.last_error.event_id == "e9"
    assert "bad envelope" in stream.health.last_error.reason


def test_accepted_event_recovers_from_erroring_to_live() -> None:
    stream = EventStream()
    stream.record_rejection("e9", "bad envelope")
    stream.append(make_event("e1"))
    assert stream.health.state is StreamState.LIVE
    assert stream.health.rejected_count == 1  # history preserved
