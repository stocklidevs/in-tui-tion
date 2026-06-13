"""US3: parallel lanes — per-worker rows, independent updates, terminal state."""

from datetime import UTC, datetime
from typing import Any

from textual.app import ComposeResult

from intui.app import IntuiApp
from intui.events import Event, Scope
from intui.kit import LanesPanel
from intui.kit.state import lanes_view, taskboard_slice
from intui.state import Store, compose_reducers
from intui.widgets import MotionMode


def make_event(
    event_id: str,
    type_: str,
    *,
    lane_id: str,
    task_id: str | None = None,
    status: str | None = None,
    summary: str | None = None,
    **payload: object,
) -> Event:
    return Event(
        version="1",
        event_id=event_id,
        run_id="run-1",
        timestamp=datetime(2026, 6, 12, tzinfo=UTC),
        type=type_,
        scope=Scope(lane_id=lane_id, task_id=task_id),
        status=status,
        summary=summary,
        payload=payload,
    )


class LanesApp(IntuiApp):
    def __init__(self, *, parent_key: str | None = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.panel = LanesPanel(lanes_view(parent_key=parent_key))

    def compose(self) -> ComposeResult:
        yield self.panel


def make_app(parent_key: str | None = None) -> tuple[LanesApp, Store]:
    store = Store(compose_reducers(taskboard=taskboard_slice()))
    return LanesApp(store=store, parent_key=parent_key), store


async def test_one_lane_per_worker_with_identity_and_activity() -> None:
    app, store = make_app()
    async with app.run_test() as pilot:
        await pilot.pause()
        store.ingest(make_event("e1", "subagent_started", lane_id="l1", name="schema-worker"))
        store.ingest(make_event("e2", "subagent_started", lane_id="l2", name="service-worker"))
        store.ingest(make_event("e3", "subagent_activity", lane_id="l1", summary="drafting map"))
        await pilot.pause(0.05)
        rows = app.panel.lane_texts()
        assert len(rows) == 2
        assert any("schema-worker" in r and "drafting map" in r for r in rows)
        assert any("service-worker" in r for r in rows)


async def test_lanes_update_independently() -> None:
    app, store = make_app()
    async with app.run_test() as pilot:
        await pilot.pause()
        store.ingest(make_event("e1", "subagent_started", lane_id="l1", name="a"))
        store.ingest(make_event("e2", "subagent_started", lane_id="l2", name="b"))
        await pilot.pause(0.05)
        store.ingest(make_event("e3", "subagent_activity", lane_id="l2", summary="b is busy"))
        await pilot.pause(0.05)
        rows = {r.split("  ")[0].strip(): r for r in app.panel.lane_texts()}
        assert "b is busy" in app.panel.lane_text_for("run-1:l2")
        assert "b is busy" not in app.panel.lane_text_for("run-1:l1")
        assert rows  # both rows present


async def test_terminal_lane_shows_status_and_stops_animating() -> None:
    app, store = make_app()
    async with app.run_test() as pilot:
        await pilot.pause()
        store.ingest(make_event("e1", "subagent_started", lane_id="l1", name="worker"))
        await pilot.pause(0.05)
        assert app.panel.lane_motion("run-1:l1") is not MotionMode.STEADY
        store.ingest(make_event("e2", "subagent_completed", lane_id="l1", status="passed"))
        await pilot.pause(0.05)
        assert "done" in app.panel.lane_text_for("run-1:l1")
        assert app.panel.lane_motion("run-1:l1") is MotionMode.STEADY


async def test_scope_filtering() -> None:
    app, store = make_app(parent_key="run-1:t1")
    async with app.run_test() as pilot:
        await pilot.pause()
        store.ingest(make_event("e1", "subagent_started", lane_id="l1", task_id="t1", name="in"))
        store.ingest(make_event("e2", "subagent_started", lane_id="l2", task_id="t2", name="out"))
        await pilot.pause(0.05)
        rows = app.panel.lane_texts()
        assert len(rows) == 1
        assert "in" in rows[0]
