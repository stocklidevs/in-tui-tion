"""EventSource protocol and MemorySource."""

from datetime import UTC, datetime

from intui.events import Event, MemorySource, Scope


def make_event(event_id: str) -> Event:
    return Event(
        version="1",
        event_id=event_id,
        run_id="run-1",
        timestamp=datetime(2026, 6, 12, tzinfo=UTC),
        type="task_started",
        scope=Scope(),
    )


async def test_memory_source_yields_raw_mappings_in_order() -> None:
    raws = [
        {
            "version": "1",
            "event_id": f"e{i}",
            "run_id": "run-1",
            "timestamp": "2026-06-12T00:00:00Z",
            "type": "tick",
            "scope": {},
        }
        for i in range(3)
    ]
    seen = [raw async for raw in MemorySource(raws)]
    assert [r["event_id"] for r in seen] == ["e0", "e1", "e2"]


async def test_memory_source_accepts_event_objects() -> None:
    events = [make_event("e1"), make_event("e2")]
    seen = [raw async for raw in MemorySource(events)]
    assert [r["event_id"] for r in seen] == ["e1", "e2"]
    # Envelopes round-trip through the serialized form.
    assert all(r["version"] == "1" for r in seen)


async def test_memory_source_is_exhausted_after_iteration() -> None:
    source = MemorySource([make_event("e1")])
    assert len([raw async for raw in source]) == 1
    assert [raw async for raw in source] == []
