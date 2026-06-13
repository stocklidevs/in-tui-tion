"""US3 acceptance: keyboard -> named intent -> handler; risky -> confirm first."""

import asyncio
from typing import Any

from textual.app import ComposeResult
from textual.widgets import Static

from intui.actions import Intent
from intui.app import ConfirmScreen, IntuiApp
from intui.events import Event
from intui.state import Store, compose_reducers


def noop_reducer(state: int, event: Event) -> int:
    return state


class IntentApp(IntuiApp):
    BINDINGS = [
        ("r", "rerun", "Re-run"),
        ("x", "clear", "Clear history"),
    ]

    def compose(self) -> ComposeResult:
        yield Static("intent test app")

    def action_rerun(self) -> None:
        self.post_intent(Intent(name="rerun", payload={"target": "demo"}))

    def action_clear(self) -> None:
        self.post_intent(Intent(name="clear_history", risky=True))


def make_app() -> tuple[IntentApp, list[Intent]]:
    received: list[Intent] = []

    async def handler(intent: Intent) -> None:
        received.append(intent)

    store = Store(compose_reducers(n=(noop_reducer, 0)))
    return IntentApp(store=store, on_intent=handler), received


async def test_shortcut_delivers_named_intent_with_payload() -> None:
    app, received = make_app()
    async with app.run_test() as pilot:
        await pilot.press("r")
        await pilot.pause()
        await asyncio.sleep(0)  # let the handler worker run
        await pilot.pause()
        assert received == [Intent(name="rerun", payload={"target": "demo"})]


async def test_risky_intent_shows_confirmation_before_delivery() -> None:
    app, received = make_app()
    async with app.run_test() as pilot:
        await pilot.press("x")
        await pilot.pause()
        assert isinstance(app.screen, ConfirmScreen)
        assert received == []  # held until confirmed


async def test_confirmed_risky_intent_is_delivered() -> None:
    app, received = make_app()
    async with app.run_test() as pilot:
        await pilot.press("x")
        await pilot.pause()
        await pilot.press("y")
        await pilot.pause()
        await asyncio.sleep(0)
        await pilot.pause()
        assert received == [Intent(name="clear_history", risky=True)]
        assert not isinstance(app.screen, ConfirmScreen)


async def test_cancelled_risky_intent_is_never_delivered() -> None:
    app, received = make_app()
    async with app.run_test() as pilot:
        await pilot.press("x")
        await pilot.pause()
        await pilot.press("escape")
        await pilot.pause()
        await asyncio.sleep(0)
        await pilot.pause()
        assert received == []
        assert not isinstance(app.screen, ConfirmScreen)


async def test_all_actions_keyboard_reachable() -> None:
    app, _ = make_app()
    async with app.run_test() as pilot:
        await pilot.pause()
        bound_keys: set[str] = set()
        for binding in type(app).BINDINGS:
            key: Any = binding[0] if isinstance(binding, tuple) else binding.key
            bound_keys.add(key)
        assert {"r", "x"} <= bound_keys
