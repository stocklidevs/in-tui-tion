"""Console motion language: phase → Signal style, plus the strip's label."""

from __future__ import annotations

from intui.console.motion import CONSOLE_SIGNAL_STYLES, activity_label_view
from intui.state import Snapshot
from intui.theming import MotionMode, resolve_status_style


def test_each_phase_has_a_distinct_color_and_motion() -> None:
    for phase in ("thinking", "verifying", "waiting", "success", "failure"):
        style = resolve_status_style(phase, CONSOLE_SIGNAL_STYLES)
        assert style.glyph  # glyph present (label-beside guarantee)
        assert style.label
        assert isinstance(style.motion, MotionMode)
    # thinking/failure are the "red" family; success is not
    assert CONSOLE_SIGNAL_STYLES["thinking"].color == CONSOLE_SIGNAL_STYLES["failure"].color
    assert CONSOLE_SIGNAL_STYLES["success"].color != CONSOLE_SIGNAL_STYLES["thinking"].color


def test_activity_label_pairs_glyph_with_phase() -> None:
    snap = Snapshot(slices={"run_status": "thinking"})
    label = activity_label_view()(snap)
    assert "thinking" in label
    assert label.split()[0] != "thinking"  # a leading glyph token before the word


def test_unknown_phase_falls_back_to_idle() -> None:
    snap = Snapshot(slices={"run_status": "definitely-not-a-phase"})
    assert "idle" in activity_label_view()(snap)
