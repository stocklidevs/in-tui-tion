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


def test_resolve_command_unique_prefix_and_ambiguity() -> None:
    assert resolve_command("f") == "files"
    assert resolve_command("files") == "files"
    assert resolve_command("s") is None  # ambiguous: save / scrub
    assert resolve_command("zzz") is None
