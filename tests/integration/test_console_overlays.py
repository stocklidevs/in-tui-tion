"""Panel overlays: browsable panels open over the timeline, Esc closes."""

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


async def test_keys_open_overlays_and_escape_closes() -> None:
    app = build_console(_source())
    async with app.run_test(size=(120, 40)) as pilot:
        await _drain(app, pilot)
        for key in ("f", "m", "l", "e", "t"):
            await pilot.press(key)
            await pilot.pause(0.05)
            assert app.screen_stack[-1].__class__.__name__ == "PanelOverlay", key
            await pilot.press("escape")
            await pilot.pause(0.05)
            assert app.screen_stack[-1].__class__.__name__ != "PanelOverlay", key
        assert app.is_running
