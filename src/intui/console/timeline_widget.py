"""RunTimeline: the single-column run feed (replaces the side chat window).

Renders :func:`intui.kit.state.run_timeline_view` rows top-to-bottom in
arrival order — messages, task results, and failure callouts in one column.
Every row carries its glyph + label (Principle IV); auto-scrolls to the
latest entries.
"""

from __future__ import annotations

from typing import Any

from rich.text import Text
from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Static

from intui.kit.state import TimelineFeedView, TimelineRow
from intui.viewmodels.selector import Selector
from intui.widgets.bound import BoundContainer


class RunTimeline(BoundContainer):
    DEFAULT_CSS = """
    RunTimeline { height: 1fr; }
    RunTimeline #timeline-scroll { height: 1fr; }
    RunTimeline #timeline-body { padding: 0 1; }
    """

    def __init__(self, selector: Selector[TimelineFeedView], **kwargs: Any) -> None:
        super().__init__(selector, **kwargs)
        self._view = TimelineFeedView()

    def compose(self) -> ComposeResult:
        yield VerticalScroll(Static(id="timeline-body"), id="timeline-scroll")

    def sync_view(self, vm: TimelineFeedView) -> None:
        if self._has_new_failure(self._view.rows, vm.rows):
            self._flash()
        self._view = vm
        self.query_one("#timeline-body", Static).update(self._build_text())
        self.query_one("#timeline-scroll", VerticalScroll).scroll_end(animate=False)

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
            return Text("waiting for events…", style="dim")
        try:
            theme = getattr(self.app, "intui_theme", None)
        except Exception:  # noqa: BLE001 - rendered outside a running app (unit tests)
            theme = None
        text = Text()
        for i, row in enumerate(self._view.rows):
            if i:
                text.append("\n")
            if row.kind in ("failure", "card"):
                self._append_callout(text, row, theme, first=i == 0)
                continue
            color = self._row_color(theme, row.status)
            text.append(f"{row.glyph} ", style=color or "")
            if row.kind == "message":
                self._append_message(text, row, theme)
            else:
                text.append(row.text)
                if row.label and row.kind == "task":
                    text.append(f"  [{row.label}]", style="dim")
            self._append_elapsed(text, row)
        return text

    def _append_message(self, text: Text, row: TimelineRow, theme: Any) -> None:
        """Voice per row: the agent is the default voice; the user is bright
        and tagged ‹you›; system lines are dimmed and tagged ‹system›."""
        if row.label == "user":
            accent = self._theme_color(theme, "accent")
            text.append(row.text, style=f"bold {accent}" if accent else "bold")
            text.append("  ‹you›", style="dim")
        elif row.label == "system":
            text.append(row.text, style="dim")
            text.append("  ‹system›", style="dim")
        else:
            text.append(row.text)

    def _append_elapsed(self, text: Text, row: TimelineRow) -> None:
        if row.elapsed:
            text.append(f"  {row.elapsed}", style="dim")

    def _append_callout(self, text: Text, row: TimelineRow, theme: Any, *, first: bool) -> None:
        """Failures and summary cards render as bordered blocks: a failure is
        red and holds its detail (the assertion) right where it happened; a
        card is accent-colored and holds the run's summary metrics."""
        if row.kind == "card":
            edge = self._theme_color(theme, "accent") or ""
        else:
            edge = self._row_color(theme, "failed") or ""
        if not first:
            text.append("\n")  # breathing room above the block
        text.append("▌ ", style=edge)
        text.append(f"{row.glyph} {row.text}", style=edge)
        text.append(f"  [{row.label}]", style="dim")
        self._append_elapsed(text, row)
        for line in row.detail.splitlines():
            text.append("\n")
            text.append("▌ ", style=edge)
            text.append(f"  {line}", style="dim" if row.kind == "failure" else "")
        text.append("\n")  # and below, so it reads as a block

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
