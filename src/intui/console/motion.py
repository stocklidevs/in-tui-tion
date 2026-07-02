"""Console motion language: phase → Signal style, and the strip's text label.

Motion is meaningful (Principle V) but never the only signal — the phase-label
selector renders a glyph + word beside the strip (Principle IV). Engine-free:
this module styles the KITT strip but imports no Textual.
"""

from __future__ import annotations

from intui.state.snapshot import Snapshot
from intui.theming import MotionMode, StatusStyle
from intui.viewmodels.selector import Selector, selector

_RED = "#f85149"
_CYAN = "#39c5cf"
_AMBER = "#d29922"
_GREEN = "#3fb950"
_PURPLE = "#bc8cff"
_MUTED = "#8b949e"

#: The run phase drives the swoosh: its color IS the state (with the label
#: beside it carrying the same phase in words).
CONSOLE_SIGNAL_STYLES: dict[str, StatusStyle] = {
    "thinking": StatusStyle(color=_RED, motion=MotionMode.SWOOSH, glyph="◆", label="thinking"),
    "failure": StatusStyle(color=_RED, motion=MotionMode.PULSE, glyph="✗", label="failure"),
    "verifying": StatusStyle(color=_CYAN, motion=MotionMode.SWOOSH, glyph="◷", label="verifying"),
    "waiting": StatusStyle(color=_AMBER, motion=MotionMode.STEADY, glyph="◌", label="waiting"),
    "success": StatusStyle(color=_GREEN, motion=MotionMode.PULSE, glyph="✓", label="success"),
    "history": StatusStyle(color=_PURPLE, motion=MotionMode.STEADY, glyph="⟲", label="history"),
    "idle": StatusStyle(color=_MUTED, motion=MotionMode.STEADY, glyph="·", label="idle"),
}


def activity_label_view() -> Selector[str]:
    """A selector for the ``{glyph} {phase}`` label beside the KITT strip."""

    @selector
    def _label(snapshot: Snapshot) -> str:
        phase = str(snapshot.slice("run_status"))
        style = CONSOLE_SIGNAL_STYLES.get(phase, CONSOLE_SIGNAL_STYLES["idle"])
        return f"{style.glyph} {style.label}"

    return _label
