"""US4 acceptance: runtime theme switch; Signal transitions; non-color status."""

from datetime import UTC, datetime

from textual.app import ComposeResult

from intui.app import IntuiApp
from intui.events import Event, Scope
from intui.state import Snapshot, Store, compose_reducers
from intui.theming import DEFAULT_THEME, MotionMode, StatusStyle, Theme
from intui.viewmodels import selector
from intui.widgets import Signal

ALT_THEME = Theme(
    name="intui-light",
    palette={
        "background": "#fafafa",
        "surface": "#ffffff",
        "text": "#1f2328",
        "text-muted": "#59636e",
    },
    emphasis={"accent": "#0969da", "muted": "#d1d9e0"},
    status_colors={
        "thinking": "#cf222e",
        "waiting": "#9a6700",
        "verifying": "#1b7c83",
        "success": "#1a7f37",
        "history": "#8250df",
        "failure": "#cf222e",
    },
)

SIGNAL_STYLES = {
    "running": StatusStyle(color="thinking", motion=MotionMode.SWOOSH, glyph=">", label="working"),
    "waiting": StatusStyle(color="waiting", motion=MotionMode.PULSE, glyph="?", label="waiting"),
    "passed": StatusStyle(color="success", motion=MotionMode.STEADY, glyph="+", label="passed"),
    "failed": StatusStyle(color="failure", motion=MotionMode.STROBE, glyph="!", label="failed"),
}


def status_reducer(status: str, event: Event) -> str:
    return event.status or status


def make_event(event_id: str, status: str) -> Event:
    return Event(
        version="1",
        event_id=event_id,
        run_id="run-1",
        timestamp=datetime(2026, 6, 12, tzinfo=UTC),
        type="status_changed",
        scope=Scope(),
        status=status,
    )


@selector
def status_vm(snapshot: Snapshot) -> str:
    return snapshot.slice("status")


class ThemedApp(IntuiApp):
    def __init__(self, **kwargs: object) -> None:
        super().__init__(**kwargs)  # type: ignore[arg-type]
        self.signal = Signal(status_vm, SIGNAL_STYLES)

    def compose(self) -> ComposeResult:
        yield self.signal


def make_app() -> tuple[ThemedApp, Store]:
    store = Store(compose_reducers(status=(status_reducer, "idle")))
    return ThemedApp(store=store), store


async def test_initial_theme_is_applied() -> None:
    app, _ = make_app()
    async with app.run_test() as pilot:
        await pilot.pause()
        assert app.theme == DEFAULT_THEME.name
        assert app.intui_theme == DEFAULT_THEME


async def test_runtime_theme_switch_requires_no_widget_changes() -> None:
    app, _ = make_app()
    async with app.run_test() as pilot:
        await pilot.pause()
        app.set_theme(ALT_THEME)
        await pilot.pause()
        assert app.theme == "intui-light"
        assert app.intui_theme == ALT_THEME
        # The same widget tree is still mounted and rendering.
        assert app.signal.is_attached


async def test_signal_transitions_track_the_bound_status() -> None:
    app, store = make_app()
    async with app.run_test() as pilot:
        await pilot.pause()
        for event_id, status, glyph, label in [
            ("e1", "running", ">", "working"),
            ("e2", "waiting", "?", "waiting"),
            ("e3", "passed", "+", "passed"),
            ("e4", "failed", "!", "failed"),
        ]:
            store.ingest(make_event(event_id, status))
            await pilot.pause(0.05)  # ride out the bridge's flush throttle
            rendered = app.signal._render_frame().plain
            assert glyph in rendered, (status, rendered)
            assert label in rendered, (status, rendered)


async def test_status_distinguishable_without_color() -> None:
    app, store = make_app()
    async with app.run_test() as pilot:
        await pilot.pause()
        plains: dict[str, str] = {}
        for event_id, status in [("e1", "running"), ("e2", "passed"), ("e3", "failed")]:
            store.ingest(make_event(event_id, status))
            await pilot.pause(0.05)  # ride out the bridge's flush throttle
            # .plain strips all styling: what remains is the color-free view.
            plains[status] = app.signal._render_frame().plain
        # Each status is uniquely identifiable from text alone (SC-006).
        assert len(set(plains.values())) == len(plains)


async def test_unknown_status_renders_neutral_not_blank() -> None:
    app, store = make_app()
    async with app.run_test() as pilot:
        await pilot.pause()
        store.ingest(make_event("e1", "bizarre_status"))
        await pilot.pause()
        rendered = app.signal._render_frame().plain
        assert "unknown" in rendered
