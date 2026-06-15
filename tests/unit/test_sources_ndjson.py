"""NdjsonStreamSource: unwrap wrapped records, ignore non-event records,
surface malformed lines, accept a path and a (sync/async) line iterable."""

from __future__ import annotations

import asyncio
import contextlib
import json
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

from intui.events import NdjsonStreamSource

GOOD = {
    "version": "1",
    "event_id": "e1",
    "run_id": "r1",
    "timestamp": "2026-06-14T10:00:00Z",
    "type": "task_started",
    "scope": {"task_id": "t1"},
}


async def _collect(source: Any) -> list[dict[str, Any]]:
    return [item async for item in source]


def _drain(source: Any) -> list[dict[str, Any]]:
    return asyncio.run(_collect(source))


def test_bare_envelope_passthrough() -> None:
    out = _drain(NdjsonStreamSource([json.dumps(GOOD)]))
    assert out == [GOOD]


def test_unwraps_wrapped_record() -> None:
    wrapped = json.dumps({"type": "run_trace_event", "event": GOOD})
    out = _drain(NdjsonStreamSource([wrapped], event_record_types=("run_trace_event",)))
    assert out == [GOOD]


def test_ignores_non_event_record() -> None:
    wrapped = json.dumps({"type": "run_trace_event", "event": GOOD})
    summary = json.dumps({"type": "summary", "totals": 3})  # ignored
    out = _drain(NdjsonStreamSource([wrapped, summary], event_record_types=("run_trace_event",)))
    assert out == [GOOD]


def test_mixed_bare_and_wrapped_with_record_types() -> None:
    # With event_record_types set, plain envelopes still come through (a renderer
    # is liberal in what it accepts), wrappers are unwrapped, summaries ignored.
    lines = [
        json.dumps(GOOD),
        json.dumps({"type": "run_trace_event", "event": {**GOOD, "event_id": "e2"}}),
        json.dumps({"type": "summary", "totals": 1}),
    ]
    out = _drain(NdjsonStreamSource(lines, event_record_types=("run_trace_event",)))
    assert [e["event_id"] for e in out] == ["e1", "e2"]


def test_malformed_line_surfaced_not_raised() -> None:
    out = _drain(NdjsonStreamSource(["{not json", json.dumps(GOOD)]))
    assert out[0]["__malformed__"]
    assert out[0]["line_number"] == 1
    assert out[1] == GOOD


def test_blank_lines_skipped() -> None:
    out = _drain(NdjsonStreamSource(["", json.dumps(GOOD), "  "]))
    assert out == [GOOD]


def test_accepts_path(tmp_path: Path) -> None:
    p = tmp_path / "s.jsonl"
    p.write_text(json.dumps(GOOD) + "\n", encoding="utf-8")
    assert _drain(NdjsonStreamSource(p)) == [GOOD]


def test_accepts_async_iterable() -> None:
    async def agen() -> AsyncIterator[str]:
        yield json.dumps(GOOD)
        yield json.dumps({**GOOD, "event_id": "e2"})

    out = _drain(NdjsonStreamSource(agen()))
    assert [e["event_id"] for e in out] == ["e1", "e2"]


# --- follow / tail (016) -----------------------------------------------------


def _env(eid: str) -> dict[str, Any]:
    return {**GOOD, "event_id": eid}


def test_follow_tails_appended_lines(tmp_path: Path) -> None:
    import json as _json

    p = tmp_path / "run.jsonl"
    p.write_text(_json.dumps(_env("e1")) + "\n" + _json.dumps(_env("e2")) + "\n", encoding="utf-8")

    async def scenario() -> list[str]:
        source = NdjsonStreamSource(p, follow=True, poll_interval=0.02)
        seen: list[str] = []

        async def consume() -> None:
            async for ev in source:
                seen.append(ev["event_id"])

        task = asyncio.ensure_future(consume())
        # initial two
        for _ in range(50):
            if len(seen) >= 2:
                break
            await asyncio.sleep(0.02)
        # append two more, in one and then a partial+rest
        with p.open("a", encoding="utf-8") as f:
            f.write(_json.dumps(_env("e3")) + "\n")
            f.flush()
        await asyncio.sleep(0.05)
        with p.open("a", encoding="utf-8") as f:
            f.write(_json.dumps(_env("e4")))  # no newline yet (partial)
            f.flush()
        await asyncio.sleep(0.05)
        with p.open("a", encoding="utf-8") as f:
            f.write("\n")  # complete the partial line
            f.flush()
        for _ in range(50):
            if len(seen) >= 4:
                break
            await asyncio.sleep(0.02)
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task
        return seen

    seen = asyncio.run(scenario())
    assert seen == ["e1", "e2", "e3", "e4"]  # partial line parsed exactly once
