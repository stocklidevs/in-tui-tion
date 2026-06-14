"""Producer SDK live path: a spawned SDK producer emits to stdout and the 009
SubprocessSource consumes it — bare canonical envelopes, no adapter."""

from __future__ import annotations

import asyncio
import sys

from intui.events import SubprocessSource
from intui.events.stream import StreamState
from intui.kit.state import artifacts_slice, taskboard_slice
from intui.state import Store, compose_reducers

# A tiny SDK-based producer that emits a run to stdout, then exits.
PRODUCER = r"""
from intui import run_recorder
rec = run_recorder(run_id="r1")          # default sink = stdout
with rec.run():
    with rec.task("build", "Build") as t:
        with t.work_item("compile"):
            rec.diff("src/app.py", before="old\n", after="new\n")
    rec.evidence(pass_rate="100%")
"""


def test_live_sdk_producer_reduces_through_subprocess_source() -> None:
    store = Store(compose_reducers(taskboard=taskboard_slice(), artifacts=artifacts_slice()))
    source = SubprocessSource(
        [sys.executable, "-c", PRODUCER], event_record_types=("run_trace_event",)
    )
    health = asyncio.run(store.run(source))  # type: ignore[arg-type]
    assert health.state == StreamState.ENDED
    snap = store.snapshot
    assert {t.task_id for t in snap.slice("taskboard").tasks.values()} == {"build"}
    assert snap.slice("taskboard").work_items  # the work item reduced
    assert snap.slice("artifacts").diff is not None
    assert snap.slice("artifacts").evidence is not None
