"""US1: the bottom command menu — render, invoke, disable, risky, overflow."""

from datetime import UTC, datetime
from typing import Any

from textual.app import ComposeResult

from intui.actions import Intent
from intui.app import ConfirmScreen, IntuiApp
from intui.events import Event, Scope
from intui.kit import CommandBar
from intui.kit.state import Command, CommandRegistry
from intui.state import Store, compose_reducers


def flag_reducer(flag: bool, event: Event) -> bool:
    if event.type == "enable":
        return True
    return flag


def enable_event() -> Event:
    return Event(
        version="1",
        event_id="enable-1",
        run_id="r1",
        timestamp=datetime(2026, 6, 12, tzinfo=UTC),
        type="enable",
        scope=Scope(),
    )


def registry() -> CommandRegistry:
    return CommandRegistry(
        [
            Command(
                "approve",
                "Approve",
                Intent("approve"),
                key="a",
                available=lambda s: s.slice("ready"),
            ),
            Command("cancel", "Cancel", Intent("cancel", risky=True), key="c"),
            Command("diff", "Diff", Intent("open_diff"), key="d"),
        ]
    )


class BarApp(IntuiApp):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.received: list[Intent] = []
        self.bar = CommandBar(registry())

    def compose(self) -> ComposeResult:
        yield self.bar


def build() -> tuple[BarApp, Store]:
    store = Store(compose_reducers(ready=(flag_reducer, False)))
    received: list[Intent] = []

    async def handler(intent: Intent) -> None:
        received.append(intent)

    app = BarApp(store=store, on_intent=handler)
    app.received = received
    return app, store


async def test_bar_renders_key_and_label() -> None:
    app, _ = build()
    async with app.run_test() as pilot:
        await pilot.pause()
        text = app.bar.menu_text()
        assert "a" in text and "Approve" in text
        assert "c" in text and "Cancel" in text


async def test_key_press_delivers_intent() -> None:
    app, _ = build()
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("d")
        await pilot.pause()
        assert [i.name for i in app.received] == ["open_diff"]


async def test_disabled_command_does_not_fire() -> None:
    app, store = build()
    async with app.run_test() as pilot:
        await pilot.pause()
        # "approve" is unavailable until ready.
        assert app.bar.is_enabled("approve") is False
        await pilot.press("a")
        await pilot.pause()
        assert app.received == []
        # Becomes available; now it fires.
        store.ingest(enable_event())
        await pilot.pause(0.05)
        assert app.bar.is_enabled("approve") is True
        await pilot.press("a")
        await pilot.pause()
        assert [i.name for i in app.received] == ["approve"]


async def test_risky_command_routes_through_confirmation() -> None:
    app, _ = build()
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("c")
        await pilot.pause()
        assert isinstance(app.screen, ConfirmScreen)
        assert app.received == []
        await pilot.press("y")
        await pilot.pause()
        assert [i.name for i in app.received] == ["cancel"]


async def test_click_delivers_intent() -> None:
    app, _ = build()
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.click(app.bar.entry_widget("diff"))
        await pilot.pause()
        assert [i.name for i in app.received] == ["open_diff"]


async def test_availability_rerenders_entry() -> None:
    app, store = build()
    async with app.run_test() as pilot:
        await pilot.pause()
        assert not app.bar.is_enabled("approve")
        store.ingest(enable_event())
        await pilot.pause(0.05)
        assert app.bar.is_enabled("approve")
