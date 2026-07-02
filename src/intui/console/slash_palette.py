"""SlashPalette: live command hints docked above the floor prompt.

While the prompt holds a ``/command`` prefix, the palette shows the matching
commands with their descriptions; ↑/↓ move the highlighted selection, Enter
runs it, and clicking a suggestion runs it directly. Hidden otherwise, so the
timeline keeps the space. The palette never mutates state itself — picks go
through the app's intent path (Principle III).
"""

from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING, Any, cast

from rich.text import Text
from textual import events
from textual.widgets import Static

from intui.actions.intents import Intent

if TYPE_CHECKING:
    from intui.app import IntuiApp

#: The console's slash vocabulary: ``(name, description)``.
CONSOLE_COMMANDS: tuple[tuple[str, str], ...] = (
    ("tasks", "task tree and counters"),
    ("lanes", "subagent lanes"),
    ("files", "workspace file tree"),
    ("evidence", "evidence panel"),
    ("metrics", "process metrics"),
    ("diff", "toggle the inline diff"),
    ("scrub", "pause/resume time-travel"),
    ("save", "save the run to a replayable file"),
)


def resolve_command(
    word: str, commands: tuple[tuple[str, str], ...] = CONSOLE_COMMANDS
) -> str | None:
    """Resolve ``word`` to a command name: exact, else unique prefix, else None."""
    names = [name for name, _ in commands]
    if word in names:
        return word
    matches = [name for name in names if name.startswith(word)] if word else []
    return matches[0] if len(matches) == 1 else None


class SlashPalette(Static):
    DEFAULT_CSS = """
    SlashPalette { height: auto; max-height: 10; padding: 0 2; background: $panel; }
    """

    def __init__(self, commands: tuple[tuple[str, str], ...] = CONSOLE_COMMANDS, **kwargs: Any):
        super().__init__(**kwargs)
        self._commands = commands
        self._matches: tuple[tuple[str, str], ...] = ()
        self._selected = 0
        self.display = False

    def _matches_for(self, value: str) -> tuple[tuple[str, str], ...]:
        if not value.startswith("/"):
            return ()
        word = value[1:].split()[0].lower() if value[1:].strip() else ""
        return tuple((name, desc) for name, desc in self._commands if name.startswith(word))

    def update_filter(self, value: str) -> None:
        """Track the prompt's text: show matching commands while it's a /prefix.

        Typing (a changed match set) snaps the selection back to the lead;
        clearing the field hides the palette but keeps the selection index, so
        the submit path can still resolve what was highlighted (the input
        clears itself before the submit intent is handled).
        """
        matches = self._matches_for(value)
        if matches and matches != self._matches:
            self._selected = 0  # typing narrowed/changed the set: lead again
        self._matches = matches  # (the selection index survives a clear)
        try:  # widget side effects need a running app; the logic above does not
            self.display = bool(matches)
            if matches:
                self.update(self._build_text())
        except Exception:  # noqa: BLE001 - offline (unit tests)
            pass

    def move_selection(self, delta: int) -> None:
        """↑/↓: move the highlighted selection through the current matches."""
        if not self._matches:
            return
        self._selected = (self._selected + delta) % len(self._matches)
        with contextlib.suppress(Exception):  # offline (unit tests)
            self.update(self._build_text())

    def selected_for(self, value: str) -> str | None:
        """The command the current selection points at, for ``value``.

        Recomputed from the text (not live widget state) so it survives the
        input clearing before the submit intent arrives.
        """
        matches = self._matches_for(value)
        if not matches:
            return None
        return matches[min(self._selected, len(matches) - 1)][0]

    def on_click(self, event: events.Click) -> None:
        """Clicking a suggestion runs it (via the app's intent path)."""
        index = event.y  # one suggestion per line; padding is horizontal only
        if 0 <= index < len(self._matches):
            name = self._matches[index][0]
            cast("IntuiApp", self.app).post_intent(Intent("palette_pick", {"name": name}))

    def _build_text(self) -> Text:
        width = max(len(name) for name, _ in self._matches) + 1
        selected = min(self._selected, len(self._matches) - 1)
        text = Text()
        for i, (name, desc) in enumerate(self._matches):
            if i:
                text.append("\n")
            lead = i == selected  # what Enter runs
            text.append(f"/{name:<{width}}", style="bold reverse" if lead else "")
            text.append(f"  {desc}", style="reverse dim" if lead else "dim")
        return text

    def hint_text(self) -> str:
        return self._build_text().plain if self._matches else ""
