"""Selectable timeline rows: cursor keys, Enter activates, Esc resumes follow."""

from __future__ import annotations

from pathlib import Path

from intui.console import RunTimeline, build_console
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


async def test_arrows_move_cursor_and_escape_resumes_follow() -> None:
    app = build_console(_source())
    async with app.run_test(size=(120, 40)) as pilot:
        await _drain(app, pilot)
        tl = app.query_one(RunTimeline)
        assert tl.selected_index is None  # follow mode
        tl.focus()
        await pilot.press("up")
        await pilot.pause(0.05)
        last = len(tl._view.rows) - 1
        assert tl.selected_index == last
        await pilot.press("k")  # vim alias
        await pilot.pause(0.05)
        assert tl.selected_index == last - 1
        await pilot.press("j")
        await pilot.pause(0.05)
        assert tl.selected_index == last
        await pilot.press("escape")
        await pilot.pause(0.05)
        assert tl.selected_index is None


async def test_enter_on_failure_unfolds_the_inline_diff() -> None:
    app = build_console(_source())
    async with app.run_test(size=(120, 40)) as pilot:
        await _drain(app, pilot)
        tl = app.query_one(RunTimeline)
        tl.focus()
        fail_index = next(i for i, r in enumerate(tl._view.rows) if r.kind == "failure")
        tl.select_index(fail_index)
        await pilot.pause(0.05)
        assert app.query_one("#inline-diff").display is False
        await pilot.press("enter")
        await pilot.pause(0.05)
        assert app.query_one("#inline-diff").display is True


async def test_enter_on_card_opens_the_evidence_overlay() -> None:
    app = build_console(_source())
    async with app.run_test(size=(120, 40)) as pilot:
        await _drain(app, pilot)
        tl = app.query_one(RunTimeline)
        tl.focus()
        card_index = next(i for i, r in enumerate(tl._view.rows) if r.kind == "card")
        tl.select_index(card_index)
        await pilot.pause(0.05)
        await pilot.press("enter")
        await pilot.pause(0.05)
        overlay = app.screen_stack[-1]
        assert overlay.__class__.__name__ == "PanelOverlay"
        from intui.kit import EvidencePanel

        assert overlay.query(EvidencePanel)
        await pilot.press("escape")
        await pilot.pause(0.05)


async def test_clicking_a_row_selects_it() -> None:
    app = build_console(_source())
    async with app.run_test(size=(120, 40)) as pilot:
        await _drain(app, pilot)
        tl = app.query_one(RunTimeline)
        # click on the first row's line inside the timeline body
        await pilot.click("#timeline-body", offset=(2, tl.row_line_starts()[0]))
        await pilot.pause(0.05)
        assert tl.selected_index == 0
