"""SlashPalette: live command hints docked above the floor prompt.

While the prompt holds a ``/command`` prefix, the palette shows the matching
commands with their descriptions (first match leading — that's what a
unique-prefix submit resolves to). Hidden otherwise, so the timeline keeps
the space. Pure presentation: the palette never runs anything itself; the
prompt submit path does (Principle III).
"""

from __future__ import annotations

from typing import Any

from rich.text import Text
from textual.widgets import Static

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
        self.display = False

    def update_filter(self, value: str) -> None:
        """Track the prompt's text: show matching commands while it's a /prefix."""
        if not value.startswith("/"):
            self._matches = ()
        else:
            word = value[1:].split()[0].lower() if value[1:].strip() else ""
            self._matches = tuple(
                (name, desc) for name, desc in self._commands if name.startswith(word)
            )
        try:  # widget side effects need a running app; the logic above does not
            self.display = bool(self._matches)
            if self._matches:
                self.update(self._build_text())
        except Exception:  # noqa: BLE001 - offline (unit tests)
            pass

    def _build_text(self) -> Text:
        width = max(len(name) for name, _ in self._matches) + 1
        text = Text()
        for i, (name, desc) in enumerate(self._matches):
            if i:
                text.append("\n")
            lead = i == 0  # what a unique-prefix submit would run
            text.append(f"/{name:<{width}}", style="bold" if lead else "")
            text.append(f"  {desc}", style="dim")
        return text

    def hint_text(self) -> str:
        return self._build_text().plain if self._matches else ""
