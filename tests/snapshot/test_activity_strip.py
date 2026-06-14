"""US2: the activity strip — state -> render + label, resize, fallback."""

from datetime import UTC, datetime
from typing import Any

from textual.app import ComposeResult

from intui.app import IntuiApp
from intui.events import Event, Scope
from intui.kit import ActivityStrip
from intui.state import Snapshot, Store, compose_reducers
from intui.theming import MotionMode
from intui.viewmodels import selector


def status_reducer(status: str, event: Event) -> str:
    if event.type == "set":
        return str(event.payload["state"])
    return status


@selector
def activity_state(snapshot: Snapshot) -> str:
    return snapshot.slice("activity")


def set_event(state: str) -> Event:
    return Event(
        version="1",
        event_id=f"s-{state}",
        run_id="r1",
        timestamp=datetime(2026, 6, 13, tzinfo=UTC),
        type="set",
        scope=Scope(),
        payload={"state": state},
    )


class StripApp(IntuiApp):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.strip = ActivityStrip(activity_state)

    def compose(self) -> ComposeResult:
        yield self.strip


def build() -> tuple[StripApp, Store]:
    store = Store(compose_reducers(activity=(status_reducer, "idle")))
    return StripApp(store=store), store


async def test_states_render_with_label() -> None:
    app, store = build()
    async with app.run_test() as pilot:
        await pilot.pause()
        for state, label in [
            ("thinking", "thinking"),
            ("verifying", "verifying"),
            ("passed", "passed"),
            ("failure", "failed"),
        ]:
            store.ingest(set_event(state))
            await pilot.pause(0.05)
            assert label in app.strip.plain_text()


async def test_states_distinguishable_without_color() -> None:
    app, store = build()
    async with app.run_test() as pilot:
        await pilot.pause()
        plains = {}
        for state in ("thinking", "passed", "failure"):
            store.ingest(set_event(state))
            await pilot.pause(0.05)
            plains[state] = app.strip.plain_text()
        assert len(set(plains.values())) == 3


async def test_motion_tracks_state() -> None:
    app, store = build()
    async with app.run_test() as pilot:
        await pilot.pause()
        store.ingest(set_event("thinking"))
        await pilot.pause(0.05)
        assert app.strip.current_motion() is MotionMode.SWOOSH
        store.ingest(set_event("passed"))
        await pilot.pause(0.05)
        assert app.strip.current_motion() is MotionMode.STEADY


def test_swoosh_glow_widens_the_sweep() -> None:
    # The KITT glow radius is configurable; a wider glow lights more cells.
    from intui.viewmodels import selector

    sel = selector(lambda _snap: "thinking")
    narrow = ActivityStrip(sel, swoosh_glow=1)
    wide = ActivityStrip(sel, swoosh_glow=5)
    for s in (narrow, wide):
        s._track_width = 40
        s._frame = 20  # mid-track so the glow is not clipped at an edge
        s._status = "thinking"

    def lit(s: ActivityStrip) -> int:
        return sum(1 for c in s._render_track(s._current_style()) if c != "·")

    assert lit(wide) > lit(narrow)


async def test_fixed_track_width_is_respected() -> None:
    # An explicit track_width fixes the sweep and is not overwritten on resize.
    from intui.viewmodels import selector

    sel = selector(lambda _snap: "passed")  # steady -> track is the full width
    app_store = Store(compose_reducers(activity=(status_reducer, "passed")))

    class FixedApp(IntuiApp):
        def __init__(self, **kwargs: Any) -> None:
            super().__init__(**kwargs)
            self.strip = ActivityStrip(sel, track_width=8)

        def compose(self) -> ComposeResult:
            yield self.strip

    app = FixedApp(store=app_store)
    async with app.run_test(size=(120, 6)) as pilot:
        await pilot.pause(0.05)
        # steady track is exactly track_width cells, regardless of the 120-wide app
        assert app.strip._track_width == 8


async def test_unknown_state_neutral_fallback() -> None:
    app, store = build()
    async with app.run_test() as pilot:
        await pilot.pause()
        store.ingest(set_event("bizarre"))
        await pilot.pause(0.05)
        assert "bizarre" in app.strip.plain_text()
        assert app.strip.current_motion() is MotionMode.STEADY
