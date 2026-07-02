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

The body is a Line-API ScrollView: only the *visible* lines are ever
rendered, so a 50k-event run scrolls as cheaply as a 50-event one. A small
per-row render cache is pruned to the neighborhood of the viewport.
"""

from __future__ import annotations

import contextlib
from bisect import bisect_right
from datetime import UTC, datetime, timedelta
from typing import Any

from rich.segment import Segment
from rich.text import Text
from textual import events
from textual.app import ComposeResult
from textual.binding import Binding
from textual.geometry import Size
from textual.scroll_view import ScrollView
from textual.strip import Strip

from intui.actions.intents import Intent
from intui.events import StreamState
from intui.kit.state import TimelineFeedView, TimelineRow
from intui.viewmodels.selector import Selector
from intui.widgets.bound import BoundContainer

#: Ignore wall-clock deltas beyond this when ticking a running row — a
#: replayed old recording carries historical timestamps, not "now".
_SANE_RUNNING = timedelta(hours=1)

#: Prune the per-row render cache down to the viewport neighborhood beyond this.
_CACHE_LIMIT = 256


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


class _TimelineBody(ScrollView):
    """Line-API body: renders only the visible lines of the feed."""

    DEFAULT_CSS = """
    _TimelineBody { height: 1fr; }
    """

    def __init__(self, owner: RunTimeline, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.can_focus = False  # keys belong to the timeline's cursor
        self._owner = owner
        self._cache: dict[int, tuple[Text, ...]] = {}

    def set_feed(self, prev: tuple[TimelineRow, ...], new: tuple[TimelineRow, ...]) -> None:
        """Rows changed: drop cache entries for rows that differ, re-measure."""
        for i, row in enumerate(new):
            if i >= len(prev) or prev[i] != row:
                self._cache.pop(i, None)
        self._remeasure()

    def invalidate_row(self, index: int | None) -> None:
        if index is not None:
            self._cache.pop(index, None)
        self.refresh()

    def invalidate_active(self) -> None:
        for i, row in enumerate(self._owner.rows):
            if row.status == "active":
                self._cache.pop(i, None)
        self.refresh()

    def rendered_row_count(self) -> int:
        return len(self._cache)

    def _remeasure(self) -> None:
        total = max(self._owner.total_lines(), 1)
        self.virtual_size = Size(max(self.size.width, 1), total)
        self.refresh()

    def on_resize(self) -> None:
        self._remeasure()

    def render_line(self, y: int) -> Strip:
        scroll_x, scroll_y = self.scroll_offset
        line = y + int(scroll_y)
        width = self.size.width
        text = self._line_text(line)
        if text is None:
            return Strip.blank(width, self.rich_style)
        segments: list[Segment] = [Segment(" ")]  # left gutter
        segments.extend(text.render(self.app.console))
        strip = Strip(segments).adjust_cell_length(width, self.rich_style)
        return strip.crop(scroll_x, scroll_x + width)

    def _line_text(self, line: int) -> Text | None:
        owner = self._owner
        rows = owner.rows
        if not rows:
            return Text("waiting for events…", style="dim") if line == 0 else None
        if line < 0 or line >= owner.total_lines():
            return None
        index = owner.row_at_physical_line(line)
        lines = self._cache.get(index)
        if lines is None:
            lines = owner.render_row(index)
            self._cache[index] = lines
            self._prune(index)
        offset = line - owner.physical_start(index)
        if 0 <= offset < len(lines):
            return lines[offset]
        return None

    def _prune(self, around: int) -> None:
        if len(self._cache) <= _CACHE_LIMIT:
            return
        keep = {i for i in self._cache if abs(i - around) <= _CACHE_LIMIT // 2}
        self._cache = {i: v for i, v in self._cache.items() if i in keep}


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
    """

    def __init__(self, selector: Selector[TimelineFeedView], **kwargs: Any) -> None:
        super().__init__(selector, **kwargs)
        self._view = TimelineFeedView()
        self._selected: int | None = None  # None = live-follow mode
        self._row_starts: tuple[int, ...] = ()  # content (title) line per row
        self._phys_starts: tuple[int, ...] = ()  # first physical line per row
        self._total_lines = 0
        self._measure_rows()

    @property
    def rows(self) -> tuple[TimelineRow, ...]:
        return self._view.rows

    def compose(self) -> ComposeResult:
        yield _TimelineBody(self, id="timeline-body")

    def on_mount(self) -> None:
        # Tick running-row durations once a second while the stream is live.
        self.set_interval(1.0, self._tick_running)

    def _body(self) -> _TimelineBody:
        return self.query_one(_TimelineBody)

    def _tick_running(self) -> None:
        if not self._is_live():
            return
        if any(r.status == "active" for r in self._view.rows):
            with contextlib.suppress(Exception):
                self._body().invalidate_active()

    def _is_live(self) -> bool:
        try:
            store = self.app.store  # type: ignore[attr-defined]
            return bool(store.snapshot.health.state is StreamState.LIVE)
        except Exception:  # noqa: BLE001 - outside a running console
            return False

    def sync_view(self, vm: TimelineFeedView) -> None:
        prev = self._view.rows
        if self._has_new_failure(prev, vm.rows):
            self._flash()
        self._view = vm
        if self._selected is not None:
            self._selected = min(self._selected, len(vm.rows) - 1) if vm.rows else None
        self._measure_rows()
        body = self._body()
        body.set_feed(prev, vm.rows)
        if self._selected is None:  # follow the live end unless the user is navigating
            body.scroll_end(animate=False)

    # --- Line geometry (shared by rendering, cursor, and click mapping) ------

    def _measure_rows(self) -> None:
        starts: list[int] = []
        phys: list[int] = []
        line = 0
        for i, row in enumerate(self._view.rows):
            phys.append(line)
            if row.kind in ("failure", "card"):
                if i:  # breathing room above the block
                    line += 1
                starts.append(line)
                line += 1  # title
                if row.detail:
                    line += len(row.detail.splitlines())
                line += 1  # breathing room below
            else:
                starts.append(line)
                line += 1
        self._row_starts = tuple(starts)
        self._phys_starts = tuple(phys)
        self._total_lines = line

    def total_lines(self) -> int:
        return self._total_lines

    def physical_start(self, index: int) -> int:
        return self._phys_starts[index]

    def row_at_physical_line(self, line: int) -> int:
        return max(bisect_right(self._phys_starts, line) - 1, 0)

    def row_line_starts(self) -> tuple[int, ...]:
        """The line each row's title starts on."""
        self._measure_rows()  # derive for the current view (tests set it directly)
        return self._row_starts

    def row_at_line(self, line: int) -> int:
        """The row owning ``line`` (detail/blank lines belong to their row)."""
        self._measure_rows()
        if not self._row_starts:
            return 0
        owner = len(self._row_starts) - 1
        for i, start in enumerate(self._row_starts):
            if line < start:
                owner = max(i - 1, 0)
                break
        return owner

    # --- Cursor --------------------------------------------------------------

    @property
    def selected_index(self) -> int | None:
        return self._selected

    def move_cursor(self, delta: int) -> None:
        """Move the cursor; entering selection mode starts at the latest row."""
        if not self._view.rows:
            return
        previous = self._selected
        if self._selected is None:
            self._selected = len(self._view.rows) - 1
        else:
            self._selected = max(0, min(self._selected + delta, len(self._view.rows) - 1))
        self._repaint_cursor(previous)

    def select_index(self, index: int) -> None:
        if not self._view.rows:
            return
        previous = self._selected
        self._selected = max(0, min(index, len(self._view.rows) - 1))
        self._repaint_cursor(previous)

    def clear_cursor(self) -> None:
        previous, self._selected = self._selected, None
        with contextlib.suppress(Exception):  # offline (unit tests)
            body = self._body()
            body.invalidate_row(previous)
            body.scroll_end(animate=False)

    def _repaint_cursor(self, previous: int | None) -> None:
        with contextlib.suppress(Exception):  # offline (unit tests)
            body = self._body()
            body.invalidate_row(previous)
            body.invalidate_row(self._selected)
            if self._selected is not None and self._selected < len(self._row_starts):
                body.scroll_to(y=max(self._row_starts[self._selected] - 3, 0), animate=False)

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
        body = self._body()
        y = event.screen_y - body.content_region.y + int(body.scroll_y)
        if self._view.rows and y >= 0:
            self.select_index(self.row_at_physical_line(min(y, self._total_lines - 1)))
            self.focus()

    # --- Flash on failure -----------------------------------------------------

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
        with contextlib.suppress(Exception):
            body = self._body()
            body.styles.background = "#3a1414"
            body.styles.animate("background", value="#3a141400", duration=0.9)

    def _motion_enabled(self) -> bool:
        try:
            return str(self.app.animation_level) != "none"
        except Exception:  # noqa: BLE001 - outside a running app (unit tests)
            return False

    # --- Row rendering ---------------------------------------------------------

    def render_row(self, index: int) -> tuple[Text, ...]:
        """All physical lines of one row (blanks included), styled."""
        row = self._view.rows[index]
        theme = self._theme()
        selected = index == self._selected
        if row.kind in ("failure", "card"):
            return self._render_callout(row, theme, selected=selected, first=index == 0)
        return (self._render_simple(row, theme, selected=selected),)

    def _theme(self) -> Any:
        try:
            return getattr(self.app, "intui_theme", None)
        except Exception:  # noqa: BLE001 - rendered outside a running app (unit tests)
            return None

    def _render_simple(self, row: TimelineRow, theme: Any, *, selected: bool) -> Text:
        cursor = "reverse" if selected else ""
        text = Text()
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
        return text

    def _render_callout(
        self, row: TimelineRow, theme: Any, *, selected: bool, first: bool
    ) -> tuple[Text, ...]:
        """Failures and summary cards render as bordered blocks: a failure is
        red and holds its detail (the assertion) right where it happened; a
        card is accent-colored and holds the run's summary metrics."""
        if row.kind == "card":
            edge = self._theme_color(theme, "accent") or ""
        else:
            edge = self._row_color(theme, "failed") or ""
        cursor = "reverse" if selected else ""
        lines: list[Text] = []
        if not first:
            lines.append(Text(""))  # breathing room above the block
        title = Text()
        title.append("▌ ", style=f"{edge} {cursor}".strip())
        title.append(f"{row.glyph} {row.text}", style=f"{edge} {cursor}".strip())
        title.append(f"  [{row.label}]", style=f"dim {cursor}".strip())
        self._append_elapsed(title, row, cursor=cursor)
        lines.append(title)
        for detail_line in row.detail.splitlines():
            body = Text()
            body.append("▌ ", style=edge)
            body.append(f"  {detail_line}", style="dim" if row.kind == "failure" else "")
            lines.append(body)
        lines.append(Text(""))  # and below, so it reads as a block
        return tuple(lines)

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

    def _row_color(self, theme: Any, status: str) -> str | None:
        if theme is None:
            return None
        key = {"failed": "failure", "completed": "success", "passed": "success"}.get(status)
        return str(theme.resolve_color(key)) if key else None

    def _theme_color(self, theme: Any, token: str) -> str | None:
        if theme is None:
            return None
        return str(theme.resolve_color(token))

    # --- Introspection (apps and tests) ---------------------------------------

    def rendered_row_count(self) -> int:
        return self._body().rendered_row_count()

    def log_text(self) -> str:
        if not self._view.rows:
            return "waiting for events…"
        self._measure_rows()
        lines: list[str] = []
        for i in range(len(self._view.rows)):
            lines.extend(t.plain for t in self.render_row(i))
        return "\n".join(lines)
