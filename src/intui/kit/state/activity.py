"""Activity-state mapping for the signature KITT strip (R6, engine-free).

The overall run state maps to a swooshing/strobing style with a color and a
mandatory non-color counterpart (glyph + label). Used by the full-width
``ActivityStrip``; kept here so the mapping is unit-testable without a terminal.
"""

from __future__ import annotations

from collections.abc import Mapping

from intui.theming.signal_style import MotionMode, StatusStyle

ACTIVITY_STATES: tuple[str, ...] = (
    "thinking",
    "waiting",
    "verifying",
    "passed",
    "history",
    "failure",
    "idle",
)

ACTIVITY_STYLES: Mapping[str, StatusStyle] = {
    "thinking": StatusStyle(
        color="thinking", motion=MotionMode.SWOOSH, glyph="»", label="thinking"
    ),
    "waiting": StatusStyle(color="waiting", motion=MotionMode.PULSE, glyph="?", label="waiting"),
    "verifying": StatusStyle(
        color="verifying", motion=MotionMode.SWOOSH, glyph="≈", label="verifying"
    ),
    "passed": StatusStyle(color="success", motion=MotionMode.STEADY, glyph="✔", label="passed"),
    "history": StatusStyle(color="history", motion=MotionMode.PULSE, glyph="◆", label="history"),
    "failure": StatusStyle(color="failure", motion=MotionMode.STROBE, glyph="✘", label="failed"),
    "idle": StatusStyle(color="muted", motion=MotionMode.STEADY, glyph="·", label="idle"),
}


def activity_style(state: str) -> StatusStyle:
    """Resolve an activity state to its style; unknown states fall back to a
    neutral steady style keeping the raw name as the label (never blank)."""
    style = ACTIVITY_STYLES.get(state)
    if style is not None:
        return style
    return StatusStyle(color="muted", motion=MotionMode.STEADY, glyph="·", label=state)
