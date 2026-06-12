"""Theme tokens: complete default, lookup, equality (FR-017, data-model.md)."""

from intui.theming import DEFAULT_THEME, Theme

REQUIRED_PALETTE = {"background", "surface", "text", "text-muted"}
REQUIRED_EMPHASIS = {"accent", "muted"}
REQUIRED_STATUS = {"thinking", "waiting", "verifying", "success", "history", "failure"}


def test_default_theme_is_named() -> None:
    assert DEFAULT_THEME.name == "intui-dark"


def test_default_theme_palette_complete() -> None:
    assert set(DEFAULT_THEME.palette) >= REQUIRED_PALETTE


def test_default_theme_emphasis_complete() -> None:
    assert set(DEFAULT_THEME.emphasis) >= REQUIRED_EMPHASIS


def test_default_theme_status_colors_complete() -> None:
    assert set(DEFAULT_THEME.status_colors) >= REQUIRED_STATUS


def test_all_token_values_are_colors() -> None:
    for group in (DEFAULT_THEME.palette, DEFAULT_THEME.emphasis, DEFAULT_THEME.status_colors):
        for value in group.values():
            assert value.startswith("#") and len(value) in (4, 7), value


def test_status_color_lookup() -> None:
    assert DEFAULT_THEME.status_color("success") == DEFAULT_THEME.status_colors["success"]


def test_status_color_unknown_falls_back_to_muted() -> None:
    assert DEFAULT_THEME.status_color("nonexistent") == DEFAULT_THEME.emphasis["muted"]


def test_theme_value_equality_and_naming() -> None:
    clone = Theme(
        name=DEFAULT_THEME.name,
        palette=dict(DEFAULT_THEME.palette),
        emphasis=dict(DEFAULT_THEME.emphasis),
        status_colors=dict(DEFAULT_THEME.status_colors),
    )
    assert clone == DEFAULT_THEME
    renamed = Theme(
        name="other",
        palette=dict(DEFAULT_THEME.palette),
        emphasis=dict(DEFAULT_THEME.emphasis),
        status_colors=dict(DEFAULT_THEME.status_colors),
    )
    assert renamed != DEFAULT_THEME
