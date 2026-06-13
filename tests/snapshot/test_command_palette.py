"""US2: the command palette — open, filter, select, invoke, dismiss, empty."""

from typing import Any

from textual.app import ComposeResult
from textual.widgets import Static

from intui.actions import Intent
from intui.app import ConfirmScreen, IntuiApp
from intui.events import Event
from intui.kit import CommandPalette
from intui.kit.state import Command, CommandRegistry
from intui.state import Store, compose_reducers


def flag_reducer(flag: bool, event: Event) -> bool:
    return True if event.type == "enable" else flag


def registry() -> CommandRegistry:
    return CommandRegistry(
        [
            Command(
                "approve",
                "Approve plan",
                Intent("approve"),
                key="a",
                available=lambda s: s.slice("ready"),
            ),
            Command("cancel", "Cancel run", Intent("cancel", risky=True), key="c"),
            Command("diff", "Open diff", Intent("open_diff"), key="d"),
            Command("evidence", "Open evidence", Intent("open_evidence"), key="e"),
        ]
    )


class PaletteApp(IntuiApp):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.received: list[Intent] = []
        self.registry = registry()

    def compose(self) -> ComposeResult:
        yield Static("body")

    async def handle_intent(self, intent: Intent) -> None:
        self.received.append(intent)


def build() -> tuple[PaletteApp, Store]:
    store = Store(compose_reducers(ready=(flag_reducer, False)))
    return PaletteApp(store=store), store


async def test_palette_opens_listing_all_commands() -> None:
    app, _ = build()
    async with app.run_test() as pilot:
        await pilot.pause()
        app.open_command_palette(app.registry)
        await pilot.pause()
        assert isinstance(app.screen, CommandPalette)
        assert len(app.screen.result_rows()) == 4


async def test_typing_filters_and_ranks() -> None:
    app, _ = build()
    async with app.run_test() as pilot:
        await pilot.pause()
        app.open_command_palette(app.registry)
        await pilot.pause()
        await pilot.press("o", "p", "e", "n")  # "open"
        await pilot.pause()
        rows = app.screen.result_ids()
        assert set(rows) == {"diff", "evidence"}


async def test_keyboard_select_and_confirm_invokes() -> None:
    app, _ = build()
    async with app.run_test() as pilot:
        await pilot.pause()
        app.open_command_palette(app.registry)
        await pilot.pause()
        await pilot.press("d", "i", "f", "f")
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()
        assert [i.name for i in app.received] == ["open_diff"]
        assert not isinstance(app.screen, CommandPalette)  # closed after invoke


async def test_escape_dismisses_without_invoking() -> None:
    app, _ = build()
    async with app.run_test() as pilot:
        await pilot.pause()
        app.open_command_palette(app.registry)
        await pilot.pause()
        await pilot.press("escape")
        await pilot.pause()
        assert app.received == []
        assert not isinstance(app.screen, CommandPalette)


async def test_risky_command_confirms_from_palette() -> None:
    app, _ = build()
    async with app.run_test() as pilot:
        await pilot.pause()
        app.open_command_palette(app.registry)
        await pilot.pause()
        await pilot.press("c", "a", "n")  # "can" -> cancel
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()
        assert isinstance(app.screen, ConfirmScreen)
        assert app.received == []
        await pilot.press("y")
        await pilot.pause()
        assert [i.name for i in app.received] == ["cancel"]


async def test_unavailable_command_not_invocable() -> None:
    app, _ = build()
    async with app.run_test() as pilot:
        await pilot.pause()
        app.open_command_palette(app.registry)
        await pilot.pause()
        await pilot.press("a", "p", "p")  # approve, but unavailable (not ready)
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()
        assert app.received == []  # disabled -> not delivered


async def test_empty_state_on_no_match() -> None:
    app, _ = build()
    async with app.run_test() as pilot:
        await pilot.pause()
        app.open_command_palette(app.registry)
        await pilot.pause()
        await pilot.press("z", "z", "z", "q")
        await pilot.pause()
        assert app.screen.result_rows() == []
        assert app.screen.is_empty_state()
