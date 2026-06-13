"""US1: the task counter chip — counts, expansion, rows, empty/narrow forms."""

from pathlib import Path
from typing import Any

from textual.app import ComposeResult

from intui.app import IntuiApp
from intui.events import read_recording
from intui.kit import TaskCounterChip
from intui.kit.state import chip_view, taskboard_slice
from intui.state import Store, compose_reducers

FIXTURE = Path(__file__).parent.parent / "replay" / "fixtures" / "parallel_run.jsonl"


class ChipApp(IntuiApp):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.chip = TaskCounterChip(chip_view())

    def compose(self) -> ComposeResult:
        yield self.chip


def make_app() -> tuple[ChipApp, Store]:
    store = Store(compose_reducers(taskboard=taskboard_slice()))
    return ChipApp(store=store), store


def replay_into(store: Store) -> None:
    for event in read_recording(FIXTURE):
        store.ingest(event)


async def test_chip_counts_track_fixture() -> None:
    app, store = make_app()
    async with app.run_test() as pilot:
        await pilot.pause()
        replay_into(store)
        await pilot.pause(0.05)
        assert "2 / 4 tasks complete" in app.chip.header_text()


async def test_chip_empty_state() -> None:
    app, _ = make_app()
    async with app.run_test() as pilot:
        await pilot.pause()
        assert "no tasks" in app.chip.header_text()


async def test_chip_expands_via_keyboard_with_rows_and_counts() -> None:
    app, store = make_app()
    async with app.run_test() as pilot:
        await pilot.pause()
        replay_into(store)
        await pilot.pause(0.05)
        assert not app.chip.expanded
        app.chip.focus()
        await pilot.press("enter")
        await pilot.pause(0.05)
        assert app.chip.expanded
        rows = app.chip.row_texts()
        assert len(rows) == 4
        assert any("Design the schema" in r and "blocked" in r for r in rows)
        footer = app.chip.footer_text()
        assert "blocked" in footer and "done" in footer
        await pilot.press("enter")
        await pilot.pause(0.05)
        assert not app.chip.expanded


async def test_chip_expands_via_click() -> None:
    app, store = make_app()
    async with app.run_test() as pilot:
        await pilot.pause()
        replay_into(store)
        await pilot.pause(0.05)
        await pilot.click(app.chip.header_widget())
        await pilot.pause(0.05)
        assert app.chip.expanded


async def test_chip_updates_while_expanded() -> None:
    app, store = make_app()
    async with app.run_test() as pilot:
        await pilot.pause()
        replay_into(store)
        await pilot.pause(0.05)
        app.chip.focus()
        await pilot.press("enter")
        await pilot.pause(0.05)
        from tests.unit.test_kit_reduce import make_event

        store.ingest(
            make_event(
                "late-1",
                "task_completed",
                task_id="t-report",
                run_id="run-mission",
                status="passed",
            )
        )
        await pilot.pause(0.05)
        assert "3 / 4 tasks complete" in app.chip.header_text()
        assert app.chip.expanded  # expansion preserved across updates


async def test_chip_narrow_fallback_form() -> None:
    app, store = make_app()
    async with app.run_test(size=(24, 10)) as pilot:
        await pilot.pause()
        replay_into(store)
        await pilot.pause(0.05)
        header = app.chip.header_text()
        assert "2/4" in header
        assert "tasks complete" not in header
