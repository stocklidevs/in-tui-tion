"""US3: the operator console renders all four modes over the replay."""

from examples.operator_console.app import build_app
from textual.widgets import ContentSwitcher

from intui.events import StreamState


async def _drain(app: object, pilot: object) -> None:
    """Wait until the replay finishes (condition, not a fixed sleep)."""
    for _ in range(100):
        if app.store.snapshot.health.state is not StreamState.LIVE:  # type: ignore[attr-defined]
            break
        await pilot.pause(0.05)  # type: ignore[attr-defined]
    await pilot.pause()  # type: ignore[attr-defined]


async def test_console_runs_all_modes_over_replay() -> None:
    app = build_app(events_per_second=500.0)
    async with app.run_test(size=(120, 40)) as pilot:
        await _drain(app, pilot)
        # Switch through every mode by keyboard; each pane renders without error.
        for key, mode in [("1", "Plan"), ("2", "Build"), ("3", "Inspect"), ("4", "Review")]:
            await pilot.press(key)
            await pilot.pause(0.05)
            assert app.store.snapshot.slice("modes").current == mode
            switcher = app.query_one("#mode-content", ContentSwitcher)
            assert switcher.current == f"pane-{mode}"
        assert app.is_running


async def test_console_reaches_completion_and_shows_artifacts() -> None:
    app = build_app(events_per_second=500.0)
    async with app.run_test(size=(120, 40)) as pilot:
        await _drain(app, pilot)
        # The replay drove modes; final state has the run's artifacts + evidence.
        art = app.store.snapshot.slice("artifacts")
        assert art.diff is not None and len(art.diff.files) == 3
        assert art.evidence is not None
        # Conversation captured the narrative.
        convo = app.store.snapshot.slice("conversation")
        assert len(convo.entries) >= 5
        # Public-safe: the operator workdir is redacted in the evidence view.
        from intui.kit.state import evidence_view

        rows = evidence_view()(app.store.snapshot).rows
        workdir = next(r for r in rows if r.key == "workdir")
        assert "run-42" not in workdir.value
