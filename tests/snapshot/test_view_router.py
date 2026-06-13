"""US1: the ViewRouter — selected pane shows, unknown -> placeholder."""

from datetime import UTC, datetime
from typing import Any

from textual.app import ComposeResult
from textual.widgets import ContentSwitcher, Static

from intui.app import IntuiApp
from intui.events import Event, Scope
from intui.kit import ViewRouter
from intui.kit.state import view_router_view, view_slice
from intui.state import Store, compose_reducers

VIEWS = ("tasks", "diff", "evidence")


def view_selected(view: str) -> Event:
    return Event(
        version="1",
        event_id=f"v-{view}",
        run_id="r1",
        timestamp=datetime(2026, 6, 13, tzinfo=UTC),
        type="view_selected",
        scope=Scope(),
        payload={"view": view},
    )


class RouterApp(IntuiApp):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.router = ViewRouter(
            view_router_view(),
            views={
                "tasks": Static("TASKS-PANE", id="tasks-pane"),
                "diff": Static("DIFF-PANE", id="diff-pane"),
                "evidence": Static("EVIDENCE-PANE", id="evidence-pane"),
            },
        )

    def compose(self) -> ComposeResult:
        yield self.router


def build(initial: str | None = None) -> tuple[RouterApp, Store]:
    store = Store(compose_reducers(views=view_slice(VIEWS, initial)))
    return RouterApp(store=store), store


def _current(app: RouterApp) -> str | None:
    return app.router.query_one(ContentSwitcher).current


async def test_shows_initial_selected_view() -> None:
    app, _ = build()
    async with app.run_test() as pilot:
        await pilot.pause(0.05)
        assert _current(app) == "view-tasks"


async def test_selection_swaps_central_pane() -> None:
    app, store = build()
    async with app.run_test() as pilot:
        await pilot.pause(0.05)
        store.ingest(view_selected("diff"))
        await pilot.pause(0.05)
        assert _current(app) == "view-diff"
        store.ingest(view_selected("evidence"))
        await pilot.pause(0.05)
        assert _current(app) == "view-evidence"


async def test_unregistered_selection_shows_placeholder() -> None:
    # views slice includes "lanes" but the router has no pane for it
    store = Store(compose_reducers(views=view_slice(("tasks", "lanes"), "tasks")))
    app = RouterApp(store=store)
    async with app.run_test() as pilot:
        await pilot.pause(0.05)
        store.ingest(
            Event(
                version="1",
                event_id="v-lanes",
                run_id="r1",
                timestamp=datetime(2026, 6, 13, tzinfo=UTC),
                type="view_selected",
                scope=Scope(),
                payload={"view": "lanes"},
            )
        )
        await pilot.pause(0.05)
        assert _current(app) == "view-placeholder"
