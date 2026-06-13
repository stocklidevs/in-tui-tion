"""Activity-state mapping for the KITT strip (R6, engine-free)."""

from intui.kit.state import ACTIVITY_STATES, ACTIVITY_STYLES, activity_style
from intui.theming import MotionMode


def test_all_r6_states_present() -> None:
    assert set(ACTIVITY_STATES) == {
        "thinking",
        "waiting",
        "verifying",
        "passed",
        "history",
        "failure",
        "idle",
    }


def test_every_state_has_distinct_glyph_and_label() -> None:
    glyphs = {ACTIVITY_STYLES[s].glyph for s in ACTIVITY_STATES}
    labels = {ACTIVITY_STYLES[s].label for s in ACTIVITY_STATES}
    assert len(glyphs) == len(ACTIVITY_STATES)
    assert len(labels) == len(ACTIVITY_STATES)


def test_motion_per_state() -> None:
    assert ACTIVITY_STYLES["thinking"].motion is MotionMode.SWOOSH
    assert ACTIVITY_STYLES["verifying"].motion is MotionMode.SWOOSH
    assert ACTIVITY_STYLES["waiting"].motion is MotionMode.PULSE
    assert ACTIVITY_STYLES["history"].motion is MotionMode.PULSE
    assert ACTIVITY_STYLES["failure"].motion is MotionMode.STROBE
    assert ACTIVITY_STYLES["passed"].motion is MotionMode.STEADY
    assert ACTIVITY_STYLES["idle"].motion is MotionMode.STEADY


def test_activity_style_resolves_known() -> None:
    assert activity_style("thinking") is ACTIVITY_STYLES["thinking"]


def test_activity_style_unknown_falls_back_with_raw_label() -> None:
    style = activity_style("weird_state")
    assert style.motion is MotionMode.STEADY
    assert style.label == "weird_state"
    assert style.glyph  # non-empty counterpart
