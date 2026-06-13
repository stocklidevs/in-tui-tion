"""US1: the prompt input — submit posts an intent + clears, no empty submit."""

from typing import Any

from textual.app import ComposeResult
from textual.widgets import Input

from intui.actions import Intent
from intui.app import IntuiApp
from intui.kit import PromptInput
from intui.state import Store, compose_reducers


class PromptApp(IntuiApp):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.received: list[Intent] = []
        self.prompt = PromptInput()

    def compose(self) -> ComposeResult:
        yield self.prompt

    async def handle_intent(self, intent: Intent) -> None:
        self.received.append(intent)


def build() -> PromptApp:
    store = Store(compose_reducers(n=(lambda s, e: s, 0)))
    return PromptApp(store=store)


async def test_submit_posts_intent_and_clears() -> None:
    app = build()
    async with app.run_test() as pilot:
        await pilot.pause()
        app.prompt.query_one(Input).focus()
        await pilot.press("h", "i")
        await pilot.press("enter")
        await pilot.pause(0.05)
        assert [i.name for i in app.received] == ["prompt_submitted"]
        assert app.received[0].payload["text"] == "hi"
        assert app.prompt.query_one(Input).value == ""  # cleared


async def test_empty_submit_does_nothing() -> None:
    app = build()
    async with app.run_test() as pilot:
        await pilot.pause()
        app.prompt.query_one(Input).focus()
        await pilot.press("enter")  # empty
        await pilot.pause(0.05)
        await pilot.press("space", "space", "enter")  # whitespace only
        await pilot.pause(0.05)
        assert app.received == []


async def test_prompt_is_keyboard_focusable() -> None:
    app = build()
    async with app.run_test() as pilot:
        await pilot.pause()
        app.prompt.query_one(Input).focus()
        await pilot.pause()
        assert app.prompt.query_one(Input).has_focus
