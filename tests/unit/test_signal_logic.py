"""Signal status-style resolution: pure, engine-free logic (FR-018).

Every status style MUST carry a non-color counterpart (glyph + label) so
status never depends on color alone (Principle IV, SC-006).
"""

import dataclasses

import pytest

from intui.theming import MotionMode, StatusStyle, resolve_status_style

STYLES = {
    "working": StatusStyle(color="thinking", motion=MotionMode.SWOOSH, glyph=">", label="working"),
    "waiting": StatusStyle(color="waiting", motion=MotionMode.PULSE, glyph="?", label="waiting"),
    "passed": StatusStyle(color="success", motion=MotionMode.STEADY, glyph="+", label="passed"),
    "failed": StatusStyle(color="failure", motion=MotionMode.STROBE, glyph="!", label="failed"),
}


def test_known_status_resolves_to_its_style() -> None:
    assert resolve_status_style("working", STYLES) is STYLES["working"]
    assert resolve_status_style("failed", STYLES) is STYLES["failed"]


def test_unknown_status_falls_back_to_neutral_style() -> None:
    style = resolve_status_style("mystery", STYLES)
    assert style.motion is MotionMode.STEADY
    assert style.glyph and style.label  # counterparts still mandatory


def test_glyph_counterpart_is_mandatory() -> None:
    with pytest.raises(ValueError, match="glyph"):
        StatusStyle(color="success", motion=MotionMode.STEADY, glyph="", label="ok")


def test_label_counterpart_is_mandatory() -> None:
    with pytest.raises(ValueError, match="label"):
        StatusStyle(color="success", motion=MotionMode.STEADY, glyph="+", label="")


def test_motion_modes_exist() -> None:
    assert {m.name for m in MotionMode} == {"STEADY", "PULSE", "SWOOSH", "STROBE"}


def test_status_style_is_immutable() -> None:
    style = STYLES["passed"]
    with pytest.raises(dataclasses.FrozenInstanceError):
        style.color = "other"  # type: ignore[misc]
