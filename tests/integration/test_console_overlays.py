"""Panel overlays: browsable panels open over the timeline, Esc closes."""

from __future__ import annotations

from pathlib import Path

from intui.console import build_console
from intui.events import NdjsonStreamSource, StreamState

RECORDING = (
    Path(__file__).parent.parent.parent / "examples" / "operator_console" / "recording.jsonl"
)


def _source() -> NdjsonStreamSource:
    return NdjsonStreamSource(RECORDING, event_record_types=("run_trace_event",), rate=2000.0)


async def _drain(app: object, pilot: object) -> None:
    for _ in range(200):
        if app.store.snapshot.health.state is not StreamState.LIVE:  # type: ignore[attr-defined]
            break
        await pilot.pause(0.02)  # type: ignore[attr-defined]
    await pilot.pause()  # type: ignore[attr-defined]


async def test_slash_commands_from_prompt_open_overlays_and_toggle_diff() -> None:
    from intui.actions import Intent

    app = build_console(_source())
    async with app.run_test(size=(120, 40)) as pilot:
        await _drain(app, pilot)
        # a slash command routes to the overlay, like the key
        await app.handle_intent(Intent("prompt_submitted", {"text": "/files"}))
        await pilot.pause(0.05)
        assert app.screen_stack[-1].__class__.__name__ == "PanelOverlay"
        await pilot.press("escape")
        await pilot.pause(0.05)
        # /diff toggles the inline region
        await app.handle_intent(Intent("prompt_submitted", {"text": "/diff"}))
        await pilot.pause(0.05)
        assert app.query_one("#inline-diff").display is True
        # plain text becomes a user message on the timeline
        before = len(app.store.snapshot.slice("conversation").entries)
        await app.handle_intent(Intent("prompt_submitted", {"text": "hello run"}))
        await pilot.pause(0.05)
        after = app.store.snapshot.slice("conversation").entries
        assert len(after) == before + 1 and after[-1].text == "hello run"


async def test_typing_slash_shows_palette_and_prefix_submit_resolves() -> None:
    from textual.widgets import Input

    from intui.console.slash_palette import SlashPalette

    app = build_console(_source())
    async with app.run_test(size=(120, 40)) as pilot:
        await _drain(app, pilot)
        palette = app.query_one(SlashPalette)
        field = app.query_one("#prompt-field", Input)
        assert palette.display is False
        field.value = "/f"
        await pilot.pause(0.05)
        assert palette.display is True
        assert "/files" in palette.hint_text()
        # submitting the unique prefix resolves to the command
        field.focus()
        await pilot.press("enter")
        await pilot.pause(0.05)
        assert app.screen_stack[-1].__class__.__name__ == "PanelOverlay"
        await pilot.press("escape")
        await pilot.pause(0.05)
        # the input cleared on submit, so the palette hides again
        assert palette.display is False


async def test_arrow_down_then_enter_runs_the_selected_command() -> None:
    from textual.widgets import Input

    from intui.kit import LanesPanel

    app = build_console(_source())
    async with app.run_test(size=(120, 40)) as pilot:
        await _drain(app, pilot)
        field = app.query_one("#prompt-field", Input)
        field.focus()
        await pilot.press("slash")  # "/" -> all commands, tasks selected
        await pilot.press("down")  # -> lanes
        await pilot.press("enter")
        await pilot.pause(0.05)
        overlay = app.screen_stack[-1]
        assert overlay.__class__.__name__ == "PanelOverlay"
        assert overlay.query(LanesPanel)  # the SELECTED command ran, not the first
        await pilot.press("escape")
        await pilot.pause(0.05)


async def test_clicking_a_suggestion_runs_it() -> None:
    from textual.widgets import Input

    from intui.console.slash_palette import SlashPalette
    from intui.kit import FileTree

    app = build_console(_source())
    async with app.run_test(size=(120, 40)) as pilot:
        await _drain(app, pilot)
        field = app.query_one("#prompt-field", Input)
        field.focus()
        await pilot.press("slash")
        await pilot.pause(0.05)
        await pilot.click(SlashPalette, offset=(4, 2))  # row 2 = files
        await pilot.pause(0.05)
        overlay = app.screen_stack[-1]
        assert overlay.__class__.__name__ == "PanelOverlay"
        assert overlay.query(FileTree)
        # the prompt cleared, so the palette is gone
        assert field.value == ""


async def test_tab_completes_the_palette_selection() -> None:
    from textual.widgets import Input

    app = build_console(_source())
    async with app.run_test(size=(120, 40)) as pilot:
        await _drain(app, pilot)
        field = app.query_one("#prompt-field", Input)
        field.focus()
        await pilot.press("slash", "f")
        await pilot.pause(0.05)
        await pilot.press("tab")
        await pilot.pause(0.05)
        assert field.value == "/files"
        # with the palette hidden, tab does NOT touch the field
        field.value = "plain note"
        await pilot.pause(0.05)
        await pilot.press("tab")
        await pilot.pause(0.05)
        assert field.value == "plain note"


async def test_click_outside_the_frame_dismisses_the_overlay() -> None:
    app = build_console(_source())
    async with app.run_test(size=(120, 40)) as pilot:
        await _drain(app, pilot)
        await pilot.press("f")
        await pilot.pause(0.05)
        assert app.screen_stack[-1].__class__.__name__ == "PanelOverlay"
        await pilot.click(offset=(2, 2))  # the dimmed background, outside the frame
        await pilot.pause(0.05)
        assert app.screen_stack[-1].__class__.__name__ != "PanelOverlay"
        # clicking INSIDE the frame must not dismiss
        await pilot.press("f")
        await pilot.pause(0.05)
        await pilot.click("#overlay-frame")
        await pilot.pause(0.05)
        assert app.screen_stack[-1].__class__.__name__ == "PanelOverlay"
        await pilot.press("escape")
        await pilot.pause(0.05)


async def test_close_button_dismisses_overlay_on_click() -> None:
    app = build_console(_source())
    async with app.run_test(size=(120, 40)) as pilot:
        await _drain(app, pilot)
        await pilot.press("f")
        await pilot.pause(0.05)
        overlay = app.screen_stack[-1]
        assert overlay.__class__.__name__ == "PanelOverlay"
        # a visible, clickable way out (mouse users don't know about Esc)
        assert overlay.query_one("#overlay-close") is not None
        await pilot.click("#overlay-close")
        await pilot.pause(0.05)
        assert app.screen_stack[-1].__class__.__name__ != "PanelOverlay"
        assert app.is_running


async def test_keys_open_overlays_and_escape_closes() -> None:
    app = build_console(_source())
    async with app.run_test(size=(120, 40)) as pilot:
        await _drain(app, pilot)
        for key in ("f", "m", "l", "e", "t"):
            await pilot.press(key)
            await pilot.pause(0.05)
            assert app.screen_stack[-1].__class__.__name__ == "PanelOverlay", key
            await pilot.press("escape")
            await pilot.pause(0.05)
            assert app.screen_stack[-1].__class__.__name__ != "PanelOverlay", key
        assert app.is_running
