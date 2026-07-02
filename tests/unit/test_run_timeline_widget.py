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


def test_user_and_system_messages_carry_voice_tags() -> None:
    tl = RunTimeline(run_timeline_view())
    tl._view = TimelineFeedView(
        rows=(
            TimelineRow(0, "message", "›", "agent", "planning tasks", "", ""),
            TimelineRow(1, "message", "›", "user", "sounds good", "", ""),
            TimelineRow(2, "message", "›", "system", "stream ended", "", ""),
        )
    )
    lines = tl.log_text().splitlines()
    assert not any("‹" in ln for ln in lines if "planning" in ln)  # agent = default voice
    assert any("‹you›" in ln for ln in lines if "sounds good" in ln)
    assert any("‹system›" in ln for ln in lines if "stream ended" in ln)


def test_elapsed_time_renders_as_suffix() -> None:
    tl = RunTimeline(run_timeline_view())
    tl._view = TimelineFeedView(
        rows=(TimelineRow(0, "task", "✓", "completed", "test_ok", "completed", "", "", "+4.2s"),)
    )
    line = tl.log_text().splitlines()[0]
    assert line.endswith("+4.2s")


def test_summary_card_renders_bordered_with_metrics() -> None:
    tl = RunTimeline(run_timeline_view())
    tl._view = TimelineFeedView(
        rows=(
            TimelineRow(
                0,
                "card",
                "▣",
                "summary",
                "pytest summary",
                "",
                "",
                "passed 2 · failed 1 · skipped 1",
            ),
        )
    )
    lines = tl.log_text().splitlines()
    bordered = [ln for ln in lines if ln.startswith("▌")]
    assert any("pytest summary" in ln for ln in bordered)
    assert any("passed 2" in ln for ln in bordered)


def _three_row_view() -> TimelineFeedView:
    return TimelineFeedView(
        rows=(
            TimelineRow(0, "task", "✓", "completed", "test_ok", "completed", ""),
            TimelineRow(1, "failure", "✗", "failed", "test_bad", "failed", "w1", "assert 1 == 2"),
            TimelineRow(2, "message", "›", "agent", "moving on", "", ""),
        )
    )


def test_cursor_moves_clamp_and_escape_returns_to_follow() -> None:
    tl = RunTimeline(run_timeline_view())
    tl._view = _three_row_view()
    assert tl.selected_index is None  # follow mode by default
    tl.move_cursor(-1)  # entering selection starts at the latest row
    assert tl.selected_index == 2
    tl.move_cursor(-1)
    assert tl.selected_index == 1
    tl.move_cursor(-1)
    tl.move_cursor(-1)  # clamps at the top
    assert tl.selected_index == 0
    tl.move_cursor(1)
    assert tl.selected_index == 1
    tl.clear_cursor()
    assert tl.selected_index is None


def test_row_line_map_accounts_for_callout_blanks() -> None:
    tl = RunTimeline(run_timeline_view())
    tl._view = _three_row_view()
    text = tl.log_text()
    lines = text.splitlines()
    starts = tl.row_line_starts()
    assert len(starts) == 3
    assert "test_ok" in lines[starts[0]]
    assert "test_bad" in lines[starts[1]]
    assert "moving on" in lines[starts[2]]


def test_row_at_line_maps_detail_lines_to_their_row() -> None:
    tl = RunTimeline(run_timeline_view())
    tl._view = _three_row_view()
    starts = tl.row_line_starts()
    assert tl.row_at_line(starts[1]) == 1
    assert tl.row_at_line(starts[1] + 1) == 1  # the assert-detail line
    assert tl.row_at_line(starts[0]) == 0
    assert tl.row_at_line(999) == 2  # past the end -> last row


def test_running_suffix_ticks_live_and_suppresses_stale() -> None:
    from datetime import UTC, datetime, timedelta

    from intui.console.timeline_widget import running_suffix

    now = datetime(2026, 7, 2, 12, 0, 0, tzinfo=UTC)
    assert running_suffix(now - timedelta(seconds=2.4), now) == " · 2.4s"
    assert running_suffix(now - timedelta(seconds=83), now) == " · 1m23s"
    # a replayed old recording must not show absurd wall-clock durations
    assert running_suffix(now - timedelta(days=17), now) == ""
    assert running_suffix(None, now) == ""
    assert running_suffix(now + timedelta(seconds=5), now) == ""  # clock skew


def test_detects_a_newly_arrived_failure_row() -> None:
    prev = (TimelineRow(0, "task", "✓", "completed", "ok", "completed", ""),)
    new = (
        *prev,
        TimelineRow(1, "failure", "✗", "failed", "FAILED x", "failed", ""),
    )
    assert RunTimeline._has_new_failure(prev, new) is True
    assert RunTimeline._has_new_failure(new, new) is False
    assert RunTimeline._has_new_failure((), prev) is False
