"""RunTimeline: the single-column feed widget (replaces the side chat)."""

from __future__ import annotations

from intui.console.timeline_widget import RunTimeline
from intui.kit.state import TimelineFeedView, TimelineRow, run_timeline_view


def test_build_text_shows_glyph_label_and_text() -> None:
    tl = RunTimeline(run_timeline_view())
    tl._view = TimelineFeedView(
        rows=(
            TimelineRow(0, "task", "✓", "completed", "test_ok", "completed", ""),
            TimelineRow(1, "failure", "✗", "failed", "FAILED test_bad", "failed", ""),
        )
    )
    text = tl.log_text()
    assert "✓" in text and "completed" in text and "test_ok" in text
    assert "✗" in text and "FAILED test_bad" in text


def test_empty_state() -> None:
    tl = RunTimeline(run_timeline_view())
    tl._view = TimelineFeedView(rows=())
    assert "waiting for events" in tl.log_text().lower()


def test_failure_renders_as_bordered_callout_with_detail() -> None:
    tl = RunTimeline(run_timeline_view())
    tl._view = TimelineFeedView(
        rows=(
            TimelineRow(0, "task", "✓", "completed", "test_ok", "completed", ""),
            TimelineRow(1, "failure", "✗", "failed", "test_bad", "failed", "w1", "assert 1 == 2"),
            TimelineRow(2, "message", "›", "agent", "moving on", "", ""),
        )
    )
    text = tl.log_text()
    lines = text.splitlines()
    callout = [ln for ln in lines if ln.startswith("▌")]
    assert any("test_bad" in ln for ln in callout)  # the failure line is bordered
    assert any("assert 1 == 2" in ln for ln in callout)  # detail inside the callout
    assert not any("moving on" in ln for ln in callout)  # ordinary rows are not


def test_detects_a_newly_arrived_failure_row() -> None:
    prev = (TimelineRow(0, "task", "✓", "completed", "ok", "completed", ""),)
    new = (
        *prev,
        TimelineRow(1, "failure", "✗", "failed", "FAILED x", "failed", ""),
    )
    assert RunTimeline._has_new_failure(prev, new) is True
    assert RunTimeline._has_new_failure(new, new) is False
    assert RunTimeline._has_new_failure((), prev) is False
