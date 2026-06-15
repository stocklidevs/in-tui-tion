"""StoreBridge.hold/release: render a held (historical) snapshot while paused."""

from __future__ import annotations

from datetime import UTC, datetime

from textual.app import App, ComposeResult

from intui.events import Event, Scope
from intui.kit import TaskCounterChip
from intui.kit.state import chip_view, taskboard_slice
from intui.state import Store, compose_reducers
from intui.widgets.bridge import StoreBridge


def _event(eid: str, task_id: str) -> Event:
    return Event(
        version="1",
        event_id=eid,
        run_id="r1",
        timestamp=datetime(2026, 6, 14, tzinfo=UTC),
        type="task_started",
        scope=Scope(task_id=task_id),
    )


class _Harness(App[None]):
    def __init__(self, store: Store) -> None:
        super().__init__()
        self.store = store
        self.bridge = StoreBridge(store, self)

    def compose(self) -> ComposeResult:
        yield TaskCounterChip(chip_view())


async def test_hold_freezes_view_while_latest_tracks() -> None:
    store = Store(compose_reducers(taskboard=taskboard_slice()))
    store.ingest(_event("e1", "t1"))
    app = _Harness(store)
    async with app.run_test(size=(80, 24)) as pilot:
        await pilot.pause()
        chip = app.query_one(TaskCounterChip)
        assert "/ 1 tasks" in chip.header_text()

        # hold a historical snapshot (0 events)
        app.bridge.hold(store.snapshot_at(0))
        await pilot.pause()
        assert "no tasks" in chip.header_text()  # frozen at the held snapshot

        # live events keep arriving; the held view stays put
        store.ingest(_event("e2", "t2"))
        store.ingest(_event("e3", "t3"))
        await pilot.pause()
        assert "no tasks" in chip.header_text()  # still frozen

        # release -> renders the latest (now 3 tasks)
        app.bridge.release()
        await pilot.pause()
        assert "/ 3 tasks" in chip.header_text()
