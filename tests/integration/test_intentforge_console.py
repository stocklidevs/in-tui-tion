"""IntentForge adapter end-to-end on a REAL captured IF 0.9.13 stream: the
zero-config ConsoleApp lists every changed file and nests assembly work items
under their suite, with no IF-specific code."""

from __future__ import annotations

from examples.intentforge_console.app import build_app

from intui.events import StreamState
from intui.kit import ViewRouter
from intui.kit.state import diff_view, evidence_view, tree_view


async def _drain(app: object, pilot: object) -> None:
    for _ in range(300):
        if app.store.snapshot.health.state is not StreamState.LIVE:  # type: ignore[attr-defined]
            break
        await pilot.pause(0.02)  # type: ignore[attr-defined]
    await pilot.pause()  # type: ignore[attr-defined]


async def test_real_if_run_lists_all_files_and_nests_items() -> None:
    app = build_app()
    async with app.run_test(size=(120, 40)) as pilot:
        await _drain(app, pilot)
        snap = app.store.snapshot
        assert snap.health.state is StreamState.ENDED

        # Many file_diff events accumulate into all the changed files (not 1).
        files = diff_view()(snap).files
        assert len(files) >= 10

        # Assembly items nest under a synthesized parent titled by the suite id.
        tree = tree_view()(snap)
        suite = next(t for t in tree.tasks if t.title == "integration-workbench")
        assert len(suite.items) == 6
        assert all(t.title != "unassigned" for t in tree.tasks)

        # Trailing summary -> evidence.
        assert snap.slice("artifacts").evidence is not None


async def test_real_if_run_navigates_views_without_crash() -> None:
    app = build_app()
    async with app.run_test(size=(120, 40)) as pilot:
        await _drain(app, pilot)
        for key, view in [("t", "tasks"), ("d", "diff"), ("e", "evidence")]:
            await pilot.press(key)
            await pilot.pause(0.05)
            assert app.query_one(ViewRouter).current_view() == view
        rows = evidence_view()(app.store.snapshot).rows
        assert any(r.key == "certified_level" for r in rows)
        assert app.is_running
