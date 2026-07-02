"""Feed virtualization: only visible rows are rendered, however big the run."""

from __future__ import annotations

from intui.console import RunTimeline, build_console
from intui.events import MemorySource, StreamState

N_ITEMS = 5000


def _big_stream() -> MemorySource:
    lines = []
    for i in range(N_ITEMS):
        lines.append(
            {
                "version": "1",
                "event_id": f"s{i}",
                "run_id": "r",
                "timestamp": "2026-07-02T10:00:00Z",
                "type": "work_item_started",
                "scope": {"task_id": "m.py", "work_item_id": f"w{i}"},
                "payload": {"name": f"item_{i}"},
            }
        )
    return MemorySource(lines)


async def _drain(app: object, pilot: object) -> None:
    for _ in range(600):
        if app.store.snapshot.health.state is not StreamState.LIVE:  # type: ignore[attr-defined]
            break
        await pilot.pause(0.02)  # type: ignore[attr-defined]
    await pilot.pause()  # type: ignore[attr-defined]


async def test_only_visible_rows_are_rendered() -> None:
    app = build_console(_big_stream())
    async with app.run_test(size=(120, 40)) as pilot:
        await _drain(app, pilot)
        tl = app.query_one(RunTimeline)
        assert len(tl._view.rows) == N_ITEMS
        # the per-row render cache holds only what was actually painted —
        # a small multiple of the viewport, never the whole feed
        assert 0 < tl.rendered_row_count() < 400
        # navigation still works at this size
        tl.focus()
        await pilot.press("up")
        await pilot.pause(0.05)
        assert tl.selected_index == N_ITEMS - 1
