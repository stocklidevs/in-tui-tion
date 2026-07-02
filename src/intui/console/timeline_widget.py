"""RunTimeline: the single-column run feed (replaces the side chat window).

Renders :func:`intui.kit.state.run_timeline_view` rows top-to-bottom in
arrival order — messages, task results, and failure callouts in one column.
Every row carries its glyph + label (Principle IV).

The timeline is an instrument, not just a display: ↑/↓ (or j/k) move a
cursor through the rows (which pauses auto-follow, like ``less +F``), Enter
activates the selected row (a failure unfolds the inline diff, the summary
card opens evidence), a click selects, and Esc returns to live-follow. The
widget only ever *posts intents* on activation — acting is the app's job
(Principle III).
"""

from __future__ import annotations

import contextlib
from datetime import UTC, datetime, timedelta
from typing import Any

from rich.text import Text
from textual import events
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import VerticalScroll
from textual.widgets import Static

from intui.actions.intents import Intent
from intui.events import StreamState
from intui.kit.state import TimelineFeedView, TimelineRow
from intui.viewmodels.selector import Selector
from intui.widgets.bound import BoundContainer

#: Ignore wall-clock deltas beyond this when ticking a running row — a
#: replayed old recording carries historical timestamps, not "now".
_SANE_RUNNING = timedelta(hours=1)


def running_suffix(at: datetime | None, now: datetime) -> str:
    """`` · 2.4s`` for a row that started ``at`` and is still running.

    Empty when there is no start time, the delta is negative (clock skew), or
    the delta is implausibly large (replaying a historical recording).
    """
    if at is None:
        return ""
    delta = now - at
    if delta < timedelta(0) or delta > _SANE_RUNNING:
        return ""
    seconds = delta.total_seconds()
    if seconds >= 60:
        minutes, rest = divmod(int(seconds), 60)
        return f" · {minutes}m{rest:02d}s"
    return f" · {seconds:.1f}s"


class RunTimeline(BoundContainer):
    can_focus = True

    BINDINGS = [
        Binding("up,k", "cursor(-1)", "Row up", show=False),
        Binding("down,j", "cursor(1)", "Row down", show=False),
        Binding("enter", "activate", "Open", show=False),
        Binding("escape", "follow", "Live", show=False),
    ]

    DEFAULT_CSS = """
    RunTimeline { height: 1fr; }
    RunTimeline #timeline-scroll { height: 1fr; }
    RunTimeline #timeline-body { padding: 0 1; }
    """

    def __init__(self, selector: Selector[TimelineFeedView], **kwargs: Any) -> None:
        super().__init__(selector, **kwargs)
        self._view = TimelineFeedView()
        self._selected: int | None = None  # None = live-follow mode
        self._row_lines: tuple[int, ...] = ()

    def compose(self) -> ComposeResult:
        scroll = VerticalScroll(Static(id="timeline-body"), id="timeline-scroll")
        scroll.can_focus = False  # keys belong to the timeline's cursor
        yield scroll

    def on_mount(self) -> None:
        # Tick running-row durations once a second while the stream is live.
        self.set_interval(1.0, self._tick_running)

    def _tick_running(self) -> None:
        if not self._is_live():
            return
        if any(r.status == "active" for r in self._view.rows):
            with contextlib.suppress(Exception):
                self.query_one("#timeline-body", Static).update(self._build_text())

    def _is_live(self) -> bool:
        try:
            store = self.app.store  # type: ignore[attr-defined]
            return bool(store.snapshot.health.state is StreamState.LIVE)
        except Exception:  # noqa: BLE001 - outside a running console
            return False

    def sync_view(self, vm: TimelineFeedView) -> None:
        if self._has_new_failure(self._view.rows, vm.rows):
            self._flash()
        self._view = vm
        if self._selected is not None:
            self._selected = min(self._selected, len(vm.rows) - 1) if vm.rows else None
        self.query_one("#timeline-body", Static).update(self._build_text())
        if self._selected is None:  # follow the live end unless the user is navigating
            self.query_one("#timeline-scroll", VerticalScroll).scroll_end(animate=False)

    # --- Cursor --------------------------------------------------------------

    @property
    def selected_index(self) -> int | None:
        return self._selected

    def move_cursor(self, delta: int) -> None:
        """Move the cursor; entering selection mode starts at the latest row."""
        if not self._view.rows:
            return
        if self._selected is None:
            self._selected = len(self._view.rows) - 1
        else:
            self._selected = max(0, min(self._selected + delta, len(self._view.rows) - 1))
        self._repaint_cursor()

    def select_index(self, index: int) -> None:
        if not self._view.rows:
            return
        self._selected = max(0, min(index, len(self._view.rows) - 1))
        self._repaint_cursor()

    def clear_cursor(self) -> None:
        self._selected = None
        with contextlib.suppress(Exception):  # offline (unit tests)
            self.query_one("#timeline-body", Static).update(self._build_text())
            self.query_one("#timeline-scroll", VerticalScroll).scroll_end(animate=False)

    def _repaint_cursor(self) -> None:
        with contextlib.suppress(Exception):  # offline (unit tests)
            self.query_one("#timeline-body", Static).update(self._build_text())
            if self._selected is not None and self._selected < len(self._row_lines):
                scroll = self.query_one("#timeline-scroll", VerticalScroll)
                scroll.scroll_to(y=max(self._row_lines[self._selected] - 3, 0), animate=False)

    def action_cursor(self, delta: int) -> None:
        self.move_cursor(delta)

    def action_follow(self) -> None:
        self.clear_cursor()

    def action_activate(self) -> None:
        """Enter: act on the selected row — via the app's intent path."""
        if self._selected is None or self._selected >= len(self._view.rows):
            return
        row = self._view.rows[self._selected]
        from intui.app import IntuiApp

        app = self.app
        if isinstance(app, IntuiApp):
            app.post_intent(Intent("timeline_row", {"kind": row.kind, "ref": row.ref}))

    def on_click(self, event: events.Click) -> None:
        """Click selects the row under the pointer (content-coordinate math)."""
        scroll = self.query_one("#timeline-scroll", VerticalScroll)
        y = event.screen_y - scroll.content_region.y + int(scroll.scroll_y)
        if self._view.rows and y >= 0:
            self.select_index(self.row_at_line(y))
            self.focus()

    # --- Row/line mapping ------------------------------------------------------

    def row_line_starts(self) -> tuple[int, ...]:
        """The line each row's title starts on (rebuilt with the text)."""
        self._build_text()  # refresh the map for the current view
        return self._row_lines

    def row_at_line(self, line: int) -> int:
        """The row owning ``line`` (detail/blank lines belong to their row)."""
        self._build_text()
        owner = len(self._row_lines) - 1
        for i, start in enumerate(self._row_lines):
            if line < start:
                owner = max(i - 1, 0)
                break
        return owner

    @staticmethod
    def _has_new_failure(prev: tuple[TimelineRow, ...], new: tuple[TimelineRow, ...]) -> bool:
        """True when a failure row arrives after the feed already had content.

        The startup sync (empty -> populated) never flashes: replaying a
        recording that happens to contain failures is history, not news.
        """
        if not prev:
            return False
        prev_fail = sum(1 for r in prev if r.kind == "failure")
        new_fail = sum(1 for r in new if r.kind == "failure")
        return new_fail > prev_fail

    def _flash(self) -> None:
        """One-shot red flash when a failure lands — grabs you, then settles.

        Honors reduced motion (Textual's ``animation_level``); a failed row
        still carries its ✗ glyph + label, so motion is never the only signal
        (Principle IV).
        """
        if not self._motion_enabled():
            return
        body = self.query_one("#timeline-body", Static)
        body.styles.background = "#3a1414"
        body.styles.animate("background", value="#3a141400", duration=0.9)

    def _motion_enabled(self) -> bool:
        try:
            return str(self.app.animation_level) != "none"
        except Exception:  # noqa: BLE001 - outside a running app (unit tests)
            return False

    def _build_text(self) -> Text:
        if not self._view.rows:
            self._row_lines = ()
            return Text("waiting for events…", style="dim")
        try:
            theme = getattr(self.app, "intui_theme", None)
        except Exception:  # noqa: BLE001 - rendered outside a running app (unit tests)
            theme = None
        text = Text()
        starts: list[int] = []
        line = 0
        for i, row in enumerate(self._view.rows):
            if i:
                text.append("\n")
                line += 1
            selected = i == self._selected
            if row.kind in ("failure", "card"):
                line = self._append_callout(
                    text, row, theme, first=i == 0, line=line, starts=starts, selected=selected
                )
                continue
            starts.append(line)
            cursor = "reverse" if selected else ""
            color = self._row_color(theme, row.status)
            text.append(f"{row.glyph} ", style=f"{color or ''} {cursor}".strip())
            if row.kind == "message":
                self._append_message(text, row, theme, cursor=cursor)
            else:
                text.append(row.text, style=cursor)
                if row.label and row.kind == "task":
                    text.append(f"  [{row.label}]", style=f"dim {cursor}".strip())
                if row.status == "active" and self._is_live():
                    tick = running_suffix(row.at, datetime.now(tz=UTC))
                    if tick:
                        text.append(tick, style=f"dim {cursor}".strip())
            self._append_elapsed(text, row, cursor=cursor)
        self._row_lines = tuple(starts)
        return text

    def _append_message(self, text: Text, row: TimelineRow, theme: Any, *, cursor: str) -> None:
        """Voice per row: the agent is the default voice; the user is bright
        and tagged ‹you›; system lines are dimmed and tagged ‹system›."""
        if row.label == "user":
            accent = self._theme_color(theme, "accent")
            style = f"bold {accent}" if accent else "bold"
            text.append(row.text, style=f"{style} {cursor}".strip())
            text.append("  ‹you›", style=f"dim {cursor}".strip())
        elif row.label == "system":
            text.append(row.text, style=f"dim {cursor}".strip())
            text.append("  ‹system›", style=f"dim {cursor}".strip())
        else:
            text.append(row.text, style=cursor)

    def _append_elapsed(self, text: Text, row: TimelineRow, *, cursor: str = "") -> None:
        if row.elapsed:
            text.append(f"  {row.elapsed}", style=f"dim {cursor}".strip())

    def _append_callout(
        self,
        text: Text,
        row: TimelineRow,
        theme: Any,
        *,
        first: bool,
        line: int,
        starts: list[int],
        selected: bool,
    ) -> int:
        """Failures and summary cards render as bordered blocks: a failure is
        red and holds its detail (the assertion) right where it happened; a
        card is accent-colored and holds the run's summary metrics. Returns
        the line counter after the block."""
        if row.kind == "card":
            edge = self._theme_color(theme, "accent") or ""
        else:
            edge = self._row_color(theme, "failed") or ""
        cursor = "reverse" if selected else ""
        if not first:
            text.append("\n")  # breathing room above the block
            line += 1
        starts.append(line)
        text.append("▌ ", style=f"{edge} {cursor}".strip())
        text.append(f"{row.glyph} {row.text}", style=f"{edge} {cursor}".strip())
        text.append(f"  [{row.label}]", style=f"dim {cursor}".strip())
        self._append_elapsed(text, row, cursor=cursor)
        for detail_line in row.detail.splitlines():
            text.append("\n")
            line += 1
            text.append("▌ ", style=edge)
            text.append(f"  {detail_line}", style="dim" if row.kind == "failure" else "")
        text.append("\n")  # and below, so it reads as a block
        line += 1
        return line

    def _row_color(self, theme: Any, status: str) -> str | None:
        if theme is None:
            return None
        key = {"failed": "failure", "completed": "success", "passed": "success"}.get(status)
        return str(theme.resolve_color(key)) if key else None

    def _theme_color(self, theme: Any, token: str) -> str | None:
        if theme is None:
            return None
        return str(theme.resolve_color(token))

    def log_text(self) -> str:
        return self._build_text().plain
