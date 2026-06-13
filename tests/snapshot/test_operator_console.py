"""The operator console: modes preselect views, commands route the center,
the run completes, and prompts are acknowledged."""

from examples.operator_console.app import MODE_DEFAULT_VIEW, build_app

from intui.events import StreamState
from intui.kit import ViewRouter


async def _drain(app: object, pilot: object) -> None:
    """Wait until the replay finishes (condition, not a fixed sleep)."""
    for _ in range(100):
        if app.store.snapshot.health.state is not StreamState.LIVE:  # type: ignore[attr-defined]
            break
        await pilot.pause(0.05)  # type: ignore[attr-defined]
    await pilot.pause()  # type: ignore[attr-defined]


async def test_modes_preselect_their_default_view() -> None:
    app = build_app(events_per_second=2000.0)
    async with app.run_test(size=(120, 40)) as pilot:
        await _drain(app, pilot)
        for key, mode in [("1", "Plan"), ("2", "Build"), ("3", "Inspect"), ("4", "Review")]:
            await pilot.press(key)
            await pilot.pause(0.1)
            assert app.store.snapshot.slice("modes").current == mode
            assert app.query_one(ViewRouter).current_view() == MODE_DEFAULT_VIEW[mode]
        assert app.is_running


async def test_view_command_routes_center_without_changing_mode() -> None:
    app = build_app(events_per_second=2000.0)
    async with app.run_test(size=(120, 40)) as pilot:
        await _drain(app, pilot)
        await pilot.press("2")  # Build -> default view "tasks"
        await pilot.pause(0.1)
        assert app.query_one(ViewRouter).current_view() == "tasks"
        await pilot.press("l")  # Lanes view command
        await pilot.pause(0.1)
        assert app.query_one(ViewRouter).current_view() == "lanes"
        assert app.store.snapshot.slice("modes").current == "Build"  # mode unchanged


async def test_console_reaches_completion_and_shows_artifacts() -> None:
    app = build_app(events_per_second=2000.0)
    async with app.run_test(size=(120, 40)) as pilot:
        await _drain(app, pilot)
        art = app.store.snapshot.slice("artifacts")
        assert art.diff is not None and len(art.diff.files) == 3
        assert art.evidence is not None
        convo = app.store.snapshot.slice("conversation")
        assert len(convo.entries) >= 5
        from intui.kit.state import evidence_view

        rows = evidence_view()(app.store.snapshot).rows
        workdir = next(r for r in rows if r.key == "workdir")
        assert "run-42" not in workdir.value


async def test_prompt_submission_appears_and_is_acknowledged() -> None:
    from textual.widgets import Input

    app = build_app(events_per_second=2000.0)
    async with app.run_test(size=(120, 40)) as pilot:
        await _drain(app, pilot)
        app.query_one("PromptInput").query_one(Input).focus()
        for ch in "ship it":
            await pilot.press(ch if ch != " " else "space")
        await pilot.press("enter")
        await pilot.pause(0.05)
        convo = app.store.snapshot.slice("conversation")
        assert any(e.role == "user" and e.text == "ship it" for e in convo.entries)
        assert app.store.snapshot.slice("run_status") == "thinking"
        for _ in range(60):
            await pilot.pause(0.05)
            convo = app.store.snapshot.slice("conversation")
            if any(e.role == "agent" and "Acknowledged" in e.text for e in convo.entries):
                break
        assert any(e.role == "agent" and "Acknowledged" in e.text for e in convo.entries)
        assert app.store.snapshot.slice("run_status") == "passed"
