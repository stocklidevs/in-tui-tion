"""SubprocessSource: spawn a producer, consume its stdout ndjson live, reflect
exit as stream end; a command that cannot start surfaces as a disconnect."""

from __future__ import annotations

import asyncio
import sys

from intui.events import SubprocessSource
from intui.events.stream import StreamHealth, StreamState
from intui.kit.state import taskboard_slice
from intui.state import Store, compose_reducers

# A tiny producer: prints two canonical envelopes (one wrapped) then exits.
PRODUCER = r"""
import json
base = {"version":"1","run_id":"r1","timestamp":"2026-06-14T10:00:00Z",
        "scope":{"task_id":"t1"}}
print(json.dumps({**base, "event_id":"e1", "type":"task_started"}))
print(json.dumps({"type":"run_trace_event",
                  "event":{**base, "event_id":"e2", "type":"task_completed"}}))
print(json.dumps({"type":"summary","totals":2}))
"""


def _run(source: object) -> StreamHealth:
    store = Store(compose_reducers(taskboard=taskboard_slice()))
    return asyncio.run(store.run(source))  # type: ignore[arg-type]


def test_consumes_stdout_and_ends() -> None:
    source = SubprocessSource(
        [sys.executable, "-c", PRODUCER], event_record_types=("run_trace_event",)
    )
    health = _run(source)
    assert health.state == StreamState.ENDED


def test_reduces_events_into_store() -> None:
    store = Store(compose_reducers(taskboard=taskboard_slice()))
    source = SubprocessSource(
        [sys.executable, "-c", PRODUCER], event_record_types=("run_trace_event",)
    )
    asyncio.run(store.run(source))
    board = store.snapshot.slice("taskboard")
    assert {t.task_id for t in board.tasks.values()} == {"t1"}


def test_uncstartable_command_disconnects() -> None:
    source = SubprocessSource(["this-command-does-not-exist-xyz"])
    health = _run(source)
    assert health.state == StreamState.DISCONNECTED
