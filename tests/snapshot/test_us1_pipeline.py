"""US1 acceptance scenarios, driven headlessly through Textual's Pilot.

1. Initial state renders.
2. A new event updates the bound widget — and only widgets whose view model
   changed re-render.
3. Unknown event types neither crash nor blank the app.
"""

from datetime import UTC, datetime
from typing import Any

from textual.app import ComposeResult

from intui.app import IntuiApp
from intui.events import Event, MemorySource, Scope
from intui.state import Snapshot, Store, compose_reducers
from intui.viewmodels import selector
from intui.widgets import BoundWidget


def make_event(event_id: str, type_: str = "item_added", **payload: object) -> Event:
    return Event(
        version="1",
        event_id=event_id,
        run_id="run-1",
        timestamp=datetime(2026, 6, 12, tzinfo=UTC),
        type=type_,
        scope=Scope(),
        payload=payload,
    )


def items_reducer(items: tuple[str, ...], event: Event) -> tuple[str, ...]:
    if event.type == "item_added":
        return (*items, str(event.payload["name"]))
    return items


def title_reducer(title: str, event: Event) -> str:
    if event.type == "title_set":
        return str(event.payload["title"])
    return title


def make_store() -> Store:
    return Store(compose_reducers(items=(items_reducer, ()), title=(title_reducer, "untitled")))


@selector
def items_vm(snapshot: Snapshot) -> tuple[str, ...]:
    return snapshot.slice("items")


@selector
def title_vm(snapshot: Snapshot) -> str:
    return snapshot.slice("title")


class CountingWidget(BoundWidget):
    """Records every render_view call so tests can assert re-render behavior."""

    def __init__(self, sel: Any, **kwargs: Any) -> None:
        super().__init__(sel, **kwargs)
        self.renders: list[Any] = []

    def render_view(self, vm: Any) -> str:
        self.renders.append(vm)
        return f"{vm}"


class PipelineApp(IntuiApp):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.items_widget = CountingWidget(items_vm, id="items")
        self.title_widget = CountingWidget(title_vm, id="title")

    def compose(self) -> ComposeResult:
        yield self.title_widget
        yield self.items_widget


async def test_initial_state_renders() -> None:
    app = PipelineApp(store=make_store())
    async with app.run_test() as pilot:
        await pilot.pause()
        assert app.title_widget.renders == ["untitled"]
        assert app.items_widget.renders == [()]


async def test_new_event_updates_only_the_bound_widget() -> None:
    store = make_store()
    app = PipelineApp(store=store)
    async with app.run_test() as pilot:
        await pilot.pause()
        store.ingest(make_event("e1", name="alpha"))
        await pilot.pause()
        assert app.items_widget.renders[-1] == ("alpha",)
        # title's view model did not change: no re-render beyond the initial.
        assert app.title_widget.renders == ["untitled"]


async def test_render_coalescing_under_burst() -> None:
    store = make_store()
    app = PipelineApp(store=store)
    async with app.run_test() as pilot:
        await pilot.pause()
        for i in range(50):
            store.ingest(make_event(f"e{i}", name=f"n{i}"))
        await pilot.pause()
        # A synchronous burst coalesces into far fewer renders than events.
        assert app.items_widget.renders[-1][-1] == "n49"
        assert len(app.items_widget.renders) < 10


async def test_unknown_event_type_does_not_blank_or_crash() -> None:
    store = make_store()
    app = PipelineApp(store=store)
    async with app.run_test() as pilot:
        await pilot.pause()
        store.ingest(make_event("e1", name="alpha"))
        await pilot.pause()
        store.ingest(make_event("e2", type_="totally_unknown"))
        await pilot.pause()
        assert app.items_widget.renders[-1] == ("alpha",)
        assert app.is_running


async def test_source_drives_ui_from_app() -> None:
    store = make_store()
    events = [
        make_event("e1", type_="title_set", title="hello"),
        make_event("e2", name="alpha"),
        make_event("e3", name="beta"),
    ]
    app = PipelineApp(store=store, source=MemorySource(events))
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.pause()
        assert app.title_widget.renders[-1] == "hello"
        assert app.items_widget.renders[-1] == ("alpha", "beta")
