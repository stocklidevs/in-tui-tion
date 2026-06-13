"""US2: the two-level task tree — nesting, expansion, navigation, statuses."""

from pathlib import Path
from typing import Any

from textual.app import ComposeResult
from textual.widgets import Tree

from intui.app import IntuiApp
from intui.events import read_recording
from intui.kit import TaskTree
from intui.kit.state import UNASSIGNED_KEY, taskboard_slice, tree_view
from intui.state import Store, compose_reducers

FIXTURE = Path(__file__).parent.parent / "replay" / "fixtures" / "parallel_run.jsonl"


class TreeApp(IntuiApp):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.task_tree = TaskTree(tree_view())

    def compose(self) -> ComposeResult:
        yield self.task_tree


def make_app() -> tuple[TreeApp, Store]:
    store = Store(compose_reducers(taskboard=taskboard_slice()))
    return TreeApp(store=store), store


def replay_into(store: Store) -> None:
    for event in read_recording(FIXTURE):
        store.ingest(event)


async def test_top_level_tasks_with_status_and_hidden_items() -> None:
    app, store = make_app()
    async with app.run_test() as pilot:
        await pilot.pause()
        replay_into(store)
        await pilot.pause(0.05)
        labels = app.task_tree.task_labels()
        assert len(labels) == 5  # 4 tasks + unassigned bucket
        schema = next(label for label in labels if "Design the schema" in label)
        assert "▲" in schema and "blocked" in schema  # identifiable collapsed (US2-4)
        # Work items hidden until expanded.
        assert app.task_tree.visible_item_count() == 0


async def test_expand_reveals_work_items_indented() -> None:
    app, store = make_app()
    async with app.run_test() as pilot:
        await pilot.pause()
        replay_into(store)
        await pilot.pause(0.05)
        app.task_tree.expand_task("run-mission:t-schema")
        await pilot.pause(0.05)
        items = app.task_tree.item_labels("run-mission:t-schema")
        assert any("draft entities" in i and "done" in i for i in items)
        assert any("wire relations" in i and "failed" in i for i in items)


async def test_expansion_preserved_across_stream_updates() -> None:
    app, store = make_app()
    async with app.run_test() as pilot:
        await pilot.pause()
        replay_into(store)
        await pilot.pause(0.05)
        app.task_tree.expand_task("run-mission:t-schema")
        await pilot.pause(0.05)
        from tests.unit.test_kit_reduce import make_event

        store.ingest(
            make_event(
                "late-1",
                "work_item_started",
                task_id="t-schema",
                work_item_id="w-new",
                run_id="run-mission",
                summary="late item",
            )
        )
        await pilot.pause(0.05)
        assert app.task_tree.is_expanded("run-mission:t-schema")
        assert any("late item" in i for i in app.task_tree.item_labels("run-mission:t-schema"))


async def test_unassigned_bucket_rendered() -> None:
    app, store = make_app()
    async with app.run_test() as pilot:
        await pilot.pause()
        replay_into(store)
        await pilot.pause(0.05)
        app.task_tree.expand_task(UNASSIGNED_KEY)
        await pilot.pause(0.05)
        assert any("stray cleanup" in i for i in app.task_tree.item_labels(UNASSIGNED_KEY))


async def test_keyboard_navigation_moves_visible_cursor() -> None:
    app, store = make_app()
    async with app.run_test() as pilot:
        await pilot.pause()
        replay_into(store)
        await pilot.pause(0.05)
        inner = app.task_tree.query_one(Tree)
        inner.focus()
        await pilot.press("down")
        await pilot.pause()
        first = inner.cursor_line
        await pilot.press("down")
        await pilot.pause()
        assert inner.cursor_line != first
