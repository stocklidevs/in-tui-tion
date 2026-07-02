"""SlashPalette: live command hints above the prompt while typing a /command."""

from __future__ import annotations

from intui.console.slash_palette import CONSOLE_COMMANDS, SlashPalette, resolve_command


def _palette() -> SlashPalette:
    return SlashPalette(CONSOLE_COMMANDS)


def test_hidden_for_plain_text_and_empty() -> None:
    pal = _palette()
    pal.update_filter("hello")
    assert pal.hint_text() == ""
    pal.update_filter("")
    assert pal.hint_text() == ""


def test_bare_slash_lists_all_commands() -> None:
    pal = _palette()
    pal.update_filter("/")
    text = pal.hint_text()
    for name, _ in CONSOLE_COMMANDS:
        assert f"/{name}" in text


def test_prefix_filters_and_first_match_leads() -> None:
    pal = _palette()
    pal.update_filter("/f")
    text = pal.hint_text()
    assert "/files" in text
    assert "/tasks" not in text
    pal.update_filter("/zzz")
    assert pal.hint_text() == ""  # nothing matches -> nothing to hint


def test_arrows_move_the_selection_and_wrap() -> None:
    pal = _palette()
    pal.update_filter("/")
    assert pal.selected_for("/") == "tasks"  # first match by default
    pal.move_selection(1)
    assert pal.selected_for("/") == "lanes"
    pal.move_selection(-1)
    assert pal.selected_for("/") == "tasks"
    pal.move_selection(-1)  # wraps to the end
    assert pal.selected_for("/") == "save"


def test_typing_resets_the_selection_to_first_match() -> None:
    pal = _palette()
    pal.update_filter("/")
    pal.move_selection(2)
    pal.update_filter("/f")  # narrowed: selection snaps back to the lead
    assert pal.selected_for("/f") == "files"


def test_selected_for_survives_the_input_clearing() -> None:
    # PromptInput clears the field before the submit intent is handled, which
    # empties the live filter — the selection must still resolve from the
    # submitted text alone.
    pal = _palette()
    pal.update_filter("/s")
    pal.move_selection(1)  # scrub -> save
    pal.update_filter("")  # the clear arrives first
    assert pal.selected_for("/s") == "save"
    assert pal.selected_for("hello") is None


def test_resolve_command_unique_prefix_and_ambiguity() -> None:
    assert resolve_command("f") == "files"
    assert resolve_command("files") == "files"
    assert resolve_command("s") is None  # ambiguous: save / scrub
    assert resolve_command("zzz") is None
