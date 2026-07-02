"""Inline diff: `d` reveals the DiffViewer in the flow, not a separate view."""

from __future__ import annotations

from pathlib import Path

from intui.console import build_console
from intui.events import NdjsonStreamSource, StreamState

RECORDING = (
    Path(__file__).parent.parent.parent / "examples" / "operator_console" / "recording.jsonl"
)


def _source() -> NdjsonStreamSource:
    return NdjsonStreamSource(RECORDING, event_record_types=("run_trace_event",), rate=2000.0)


async def _drain(app: object, pilot: object) -> None:
    for _ in range(200):
        if app.store.snapshot.health.state is not StreamState.LIVE:  # type: ignore[attr-defined]
            break
        await pilot.pause(0.02)  # type: ignore[attr-defined]
    await pilot.pause()  # type: ignore[attr-defined]


async def test_d_toggles_inline_diff() -> None:
    app = build_console(_source())
    async with app.run_test(size=(120, 40)) as pilot:
        await _drain(app, pilot)
        diff = app.query_one("#inline-diff")
        assert diff.display is False
        await pilot.press("d")
        await pilot.pause(0.05)
        assert diff.display is True
        await pilot.press("d")
        await pilot.pause(0.05)
        assert diff.display is False
        assert app.is_running
