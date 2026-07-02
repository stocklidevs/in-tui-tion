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
