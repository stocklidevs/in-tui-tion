"""US1: the mode strip — render, active marker, key -> switch_mode."""

from datetime import UTC, datetime
from typing import Any

from textual.app import ComposeResult

from intui.actions import Intent
from intui.app import IntuiApp
from intui.events import Event, Scope
from intui.kit import ModeStrip
from intui.kit.state import mode_slice, mode_view
from intui.state import Store, compose_reducers

MODES = ("Plan", "Build", "Inspect", "Review")
KEYS = {"1": "Plan", "2": "Build", "3": "Inspect", "4": "Review"}


class ModeApp(IntuiApp):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.received: list[Intent] = []
        self.strip = ModeStrip(mode_view(), keys=KEYS)

    def compose(self) -> ComposeResult:
        yield self.strip

    async def handle_intent(self, intent: Intent) -> None:
        self.received.append(intent)
        if intent.name == "switch_mode":
            self.store.ingest(
                Event(
                    version="1",
                    event_id=f"mc-{len(self.received)}",
                    run_id="r1",
                    timestamp=datetime(2026, 6, 13, tzinfo=UTC),
                    type="mode_changed",
                    scope=Scope(),
                    payload={"mode": intent.payload["mode"]},
                )
            )


def build() -> tuple[ModeApp, Store]:
    store = Store(compose_reducers(modes=mode_slice(MODES)))
    return ModeApp(store=store), store


async def test_renders_modes_with_active_marked() -> None:
    app, _ = build()
    async with app.run_test() as pilot:
        await pilot.pause()
        text = app.strip.strip_text()
        assert all(m in text for m in MODES)
        assert "▸ Plan" in text  # active marker, non-color


async def test_key_posts_switch_mode_and_rehighlights() -> None:
    app, store = build()
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("3")  # Inspect
        await pilot.pause(0.05)
        assert any(
            i.name == "switch_mode" and i.payload["mode"] == "Inspect" for i in app.received
        )
        assert store.snapshot.slice("modes").current == "Inspect"
        assert "▸ Inspect" in app.strip.strip_text()


async def test_switch_to_active_mode_is_noop() -> None:
    app, store = build()
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("1")  # already Plan
        await pilot.pause(0.05)
        assert store.snapshot.slice("modes").current == "Plan"
