"""SC-003: the kit stays responsive with 500 tasks.

Counts derive from state (not from rendered rows), and chip expand / tree
interaction complete within a render frame budget.
"""

import time
from datetime import UTC, datetime
from typing import Any

from textual.app import ComposeResult

from intui.app import IntuiApp
from intui.events import Event, Scope
from intui.kit import TaskCounterChip, TaskTree
from intui.kit.state import chip_view, taskboard_slice, tree_view
from intui.state import Store, compose_reducers

N_TASKS = 500


def seed_events() -> list[Event]:
    events: list[Event] = []
    for i in range(N_TASKS):
        events.append(
            Event(
                version="1",
                event_id=f"start-{i}",
                run_id="run-scale",
                timestamp=datetime(2026, 6, 12, tzinfo=UTC),
                type="task_started",
                scope=Scope(task_id=f"t{i}"),
                summary=f"Task {i}",
            )
        )
    for i in range(0, N_TASKS, 2):
        events.append(
            Event(
                version="1",
                event_id=f"done-{i}",
                run_id="run-scale",
                timestamp=datetime(2026, 6, 12, tzinfo=UTC),
                type="task_completed",
                scope=Scope(task_id=f"t{i}"),
                status="passed",
            )
        )
    return events


class ScaleApp(IntuiApp):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.chip = TaskCounterChip(chip_view())
        self.task_tree = TaskTree(tree_view())

    def compose(self) -> ComposeResult:
        yield self.chip
        yield self.task_tree


async def test_counts_accurate_and_interaction_responsive_at_scale() -> None:
    store = Store(compose_reducers(taskboard=taskboard_slice()))
    app = ScaleApp(store=store)
    async with app.run_test() as pilot:
        await pilot.pause()
        for event in seed_events():
            store.ingest(event)
        await pilot.pause(0.1)

        # Counts derived from state, correct regardless of rendered rows.
        assert "250 / 500 tasks complete" in app.chip.header_text()

        # Expanding the chip is a single frame's work.
        app.chip.focus()
        start = time.monotonic()
        await pilot.press("enter")
        await pilot.pause()
        assert app.chip.expanded
        assert time.monotonic() - start < 1.0

        # Tree exposes all task rows and a known one expands quickly.
        assert len(app.task_tree.task_labels()) == N_TASKS
        start = time.monotonic()
        app.task_tree.expand_task("run-scale:t0")
        await pilot.pause()
        assert time.monotonic() - start < 1.0
