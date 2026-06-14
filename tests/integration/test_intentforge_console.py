"""IntentForge adapter end-to-end: the captured IF fixture renders through the
zero-config ConsoleApp with no IF-specific code."""

from __future__ import annotations

from examples.intentforge_console.app import build_app

from intui.events import StreamState
from intui.kit import ViewRouter
from intui.kit.state import evidence_view


async def _drain(app: object, pilot: object) -> None:
    for _ in range(200):
        if app.store.snapshot.health.state is not StreamState.LIVE:  # type: ignore[attr-defined]
            break
        await pilot.pause(0.02)  # type: ignore[attr-defined]
    await pilot.pause()  # type: ignore[attr-defined]


async def test_if_fixture_reduces_all_slices() -> None:
    app = build_app()
    async with app.run_test(size=(120, 40)) as pilot:
        await _drain(app, pilot)
        board = app.store.snapshot.slice("taskboard")
        assert {t.task_id for t in board.tasks.values()} == {"add-feature"}
        assert board.work_items  # assembly item became a work item
        art = app.store.snapshot.slice("artifacts")
        assert art.diff is not None and len(art.diff.files) >= 1
        assert art.evidence is not None and len(art.evidence.metrics) >= 1
        assert app.store.snapshot.slice("run_status") == "passed"  # matrix_suite_finished
        assert app.store.snapshot.health.state is StreamState.ENDED


async def test_diff_and_evidence_views_navigable() -> None:
    app = build_app()
    async with app.run_test(size=(120, 40)) as pilot:
        await _drain(app, pilot)
        await pilot.press("d")
        await pilot.pause(0.05)
        assert app.query_one(ViewRouter).current_view() == "diff"
        await pilot.press("e")
        await pilot.pause(0.05)
        assert app.query_one(ViewRouter).current_view() == "evidence"
        rows = evidence_view()(app.store.snapshot).rows
        assert any(r.key == "certified_level" for r in rows)
