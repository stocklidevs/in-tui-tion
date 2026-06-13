"""Accessibility audits: SC-004 (keyboard-only) and SC-006 (no color reliance)."""

from examples.hello_replay.app import SIGNAL_STYLES, build_app

from intui.app import ConfirmScreen


async def test_every_primary_example_action_is_keyboard_operable() -> None:
    app = build_app(events_per_second=1000.0)
    async with app.run_test() as pilot:
        await pilot.pause()
        # t: theme switch.
        before = app.intui_theme.name
        await pilot.press("t")
        await pilot.pause()
        assert app.intui_theme.name != before
        # r: re-run replay (normal intent; no prompt).
        await pilot.press("r")
        await pilot.pause()
        assert not isinstance(app.screen, ConfirmScreen)
        # x: risky clear -> confirmation prompt, confirm with y.
        await pilot.press("x")
        await pilot.pause()
        assert isinstance(app.screen, ConfirmScreen)
        await pilot.press("y")
        await pilot.pause()
        assert not isinstance(app.screen, ConfirmScreen)
        # q quits.
        await pilot.press("q")
        await pilot.pause()
    assert not app.is_running


def test_example_bindings_cover_all_primary_actions() -> None:
    from examples.hello_replay.app import HelloReplayApp

    keys = {b[0] if isinstance(b, tuple) else b.key for b in HelloReplayApp.BINDINGS}
    assert {"q", "r", "x", "t"} <= keys


def test_every_status_has_unique_non_color_identity() -> None:
    # SC-006: with color stripped, each status is still uniquely identifiable
    # by its glyph+label counterpart.
    identities = {(style.glyph, style.label) for style in SIGNAL_STYLES.values()}
    assert len(identities) == len(SIGNAL_STYLES)
    for style in SIGNAL_STYLES.values():
        assert style.glyph and style.label


# --- Kit (feature 002) accessibility ----------------------------------------


def test_kit_status_presentation_color_free_identity() -> None:
    # SC-005: every kit status is uniquely identifiable by glyph+label alone.
    from intui.kit.state import STATUS_PRESENTATION

    identities = {(s.glyph, s.label) for s in STATUS_PRESENTATION.values()}
    assert len(identities) == len(STATUS_PRESENTATION)
    for style in STATUS_PRESENTATION.values():
        assert style.glyph and style.label


async def test_command_surfaces_keyboard_only_and_risky_confirm() -> None:
    # SC-002/SC-003: commands invocable by keyboard from both surfaces; risky
    # commands confirm before delivery from each.
    from textual.app import ComposeResult
    from textual.widgets import Static

    from intui.actions import Intent
    from intui.app import ConfirmScreen, IntuiApp
    from intui.kit import CommandBar
    from intui.kit.state import Command, CommandRegistry
    from intui.state import Store, compose_reducers

    def reg() -> CommandRegistry:
        return CommandRegistry(
            [
                Command("go", "Go", Intent("go"), key="g"),
                Command("wipe", "Wipe", Intent("wipe", risky=True), key="w"),
            ]
        )

    class CmdApp(IntuiApp):
        def __init__(self, **kwargs: object) -> None:
            super().__init__(**kwargs)  # type: ignore[arg-type]
            self.received: list[str] = []
            self.reg = reg()
            self.bar = CommandBar(self.reg)

        def compose(self) -> ComposeResult:
            yield Static("body")
            yield self.bar

        async def handle_intent(self, intent: Intent) -> None:
            self.received.append(intent.name)

    store = Store(compose_reducers(n=(lambda s, e: s, 0)))
    app = CmdApp(store=store)
    async with app.run_test() as pilot:
        await pilot.pause()
        # Menu key, non-risky.
        await pilot.press("g")
        await pilot.pause()
        assert app.received == ["go"]
        # Menu key, risky -> confirm required.
        await pilot.press("w")
        await pilot.pause()
        assert isinstance(app.screen, ConfirmScreen)
        await pilot.press("y")
        await pilot.pause()
        assert app.received == ["go", "wipe"]
        # Palette path, keyboard-only.
        app.open_command_palette(app.reg)
        await pilot.pause()
        await pilot.press("g", "o")
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()
        assert app.received == ["go", "wipe", "go"]


async def test_kit_chip_keyboard_operable() -> None:
    # SC-004: the chip expands/collapses by keyboard alone.
    from textual.app import ComposeResult

    from intui.app import IntuiApp
    from intui.kit import TaskCounterChip
    from intui.kit.state import chip_view, taskboard_slice
    from intui.state import Store, compose_reducers

    class ChipOnly(IntuiApp):
        def __init__(self, **kwargs: object) -> None:
            super().__init__(**kwargs)  # type: ignore[arg-type]
            self.chip = TaskCounterChip(chip_view())

        def compose(self) -> ComposeResult:
            yield self.chip

    store = Store(compose_reducers(taskboard=taskboard_slice()))
    app = ChipOnly(store=store)
    async with app.run_test() as pilot:
        await pilot.pause()
        app.chip.focus()
        await pilot.press("enter")
        await pilot.pause()
        assert app.chip.expanded
        await pilot.press("space")
        await pilot.pause()
        assert not app.chip.expanded
