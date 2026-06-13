"""BoundContainer: selector binding + value-equality sync for containers."""

from datetime import UTC, datetime
from typing import Any

from textual.app import ComposeResult
from textual.widgets import Static

from intui.app import IntuiApp
from intui.events import Event, Scope
from intui.state import Snapshot, Store, compose_reducers
from intui.viewmodels import selector
from intui.widgets import BoundContainer


def make_event(event_id: str, **payload: object) -> Event:
    return Event(
        version="1",
        event_id=event_id,
        run_id="run-1",
        timestamp=datetime(2026, 6, 12, tzinfo=UTC),
        type="item_added",
        scope=Scope(),
        payload=payload,
    )


def items_reducer(items: tuple[str, ...], event: Event) -> tuple[str, ...]:
    if event.type == "item_added":
        return (*items, str(event.payload["name"]))
    return items


@selector
def items_vm(snapshot: Snapshot) -> tuple[str, ...]:
    return snapshot.slice("items")


class ItemsContainer(BoundContainer):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(items_vm, **kwargs)
        self.syncs: list[Any] = []

    def sync_view(self, vm: tuple[str, ...]) -> None:
        self.syncs.append(vm)
        self.remove_children()
        self.mount_all(Static(name_, classes="item") for name_ in vm)


class ContainerApp(IntuiApp):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.container = ItemsContainer()

    def compose(self) -> ComposeResult:
        yield self.container


async def test_container_syncs_children_from_view_model() -> None:
    store = Store(compose_reducers(items=(items_reducer, ())))
    app = ContainerApp(store=store)
    async with app.run_test() as pilot:
        await pilot.pause()
        store.ingest(make_event("e1", name="alpha"))
        store.ingest(make_event("e2", name="beta"))
        await pilot.pause(0.05)
        assert len(app.container.query(".item")) == 2


async def test_container_skips_sync_on_equal_view_model() -> None:
    store = Store(compose_reducers(items=(items_reducer, ())))
    app = ContainerApp(store=store)
    async with app.run_test() as pilot:
        await pilot.pause()
        baseline = len(app.container.syncs)
        # An event of an unrelated type leaves the items vm value-equal.
        unrelated = Event(
            version="1",
            event_id="x1",
            run_id="run-1",
            timestamp=datetime(2026, 6, 12, tzinfo=UTC),
            type="noop",
            scope=Scope(),
        )
        store.ingest(unrelated)
        await pilot.pause(0.05)
        assert len(app.container.syncs) == baseline
