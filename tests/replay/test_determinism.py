"""Replay determinism: the backbone guarantee (FR-003/006, SC-002).

The committed fixture is a recorded simulated run; replaying it must always
produce identical snapshots, headless or live.
"""

import asyncio
from pathlib import Path

from intui.events import Event, JsonlReplaySource, read_recording
from intui.state import Snapshot, Store, compose_reducers

FIXTURE = Path(__file__).parent / "fixtures" / "sample_run.jsonl"


def tasks_reducer(tasks: tuple[str, ...], event: Event) -> tuple[str, ...]:
    if event.type == "task_completed":
        return (*tasks, str(event.payload["name"]))
    return tasks


def status_reducer(status: str, event: Event) -> str:
    return event.status or status


def make_store() -> Store:
    return Store(compose_reducers(tasks=(tasks_reducer, ()), status=(status_reducer, "idle")))


def replay_headless() -> Snapshot:
    store = make_store()
    for event in read_recording(FIXTURE):
        store.ingest(event)
    store.mark_ended()
    return store.snapshot


def test_fixture_exists_and_is_nonempty() -> None:
    events = read_recording(FIXTURE)
    assert len(events) >= 5


def test_replay_twice_produces_identical_snapshots() -> None:
    assert replay_headless() == replay_headless()


async def test_async_source_replay_equals_headless_replay() -> None:
    headless = replay_headless()

    store = make_store()
    health = await store.run(JsonlReplaySource(FIXTURE))
    assert store.snapshot == headless
    assert health == headless.health


async def test_paced_replay_equals_unpaced_replay() -> None:
    fast = make_store()
    await fast.run(JsonlReplaySource(FIXTURE))

    paced = make_store()
    await paced.run(JsonlReplaySource(FIXTURE, rate=1000.0))

    assert fast.snapshot == paced.snapshot


def test_replay_is_deterministic_across_event_loop_runs() -> None:
    async def run_once() -> Snapshot:
        store = make_store()
        await store.run(JsonlReplaySource(FIXTURE))
        return store.snapshot

    a = asyncio.run(run_once())
    b = asyncio.run(run_once())
    assert a == b
