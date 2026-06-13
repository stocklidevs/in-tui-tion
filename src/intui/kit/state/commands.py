"""Command model: registry, availability, fuzzy matcher (engine-free).

A Command is a named action with an optional key, the Intent it emits, and a
pure availability rule over state. The registry is the single source of truth
both surfaces (bar + palette) render; ``command_view`` projects per-snapshot
enabled state, and ``match_score``/``filter_commands`` power the palette.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass, field

from intui.actions.intents import Intent
from intui.state.snapshot import Snapshot
from intui.viewmodels.selector import Selector


def _always(_snapshot: Snapshot) -> bool:
    return True


@dataclass(frozen=True, slots=True)
class Command:
    id: str
    label: str
    intent: Intent
    key: str | None = None
    available: Callable[[Snapshot], bool] = field(default=_always)

    @property
    def risky(self) -> bool:
        return self.intent.risky


class CommandRegistry:
    """Ordered commands keyed by id; the single source both surfaces render."""

    def __init__(self, commands: Iterable[Command]) -> None:
        ordered = tuple(commands)
        seen: set[str] = set()
        for command in ordered:
            if command.id in seen:
                raise ValueError(f"duplicate command id: {command.id!r}")
            seen.add(command.id)
        self._commands = ordered
        self._by_id = {c.id: c for c in ordered}

    @property
    def commands(self) -> tuple[Command, ...]:
        return self._commands

    def get(self, command_id: str) -> Command:
        return self._by_id[command_id]

    def is_available(self, command_id: str, snapshot: Snapshot) -> bool:
        return self._by_id[command_id].available(snapshot)


@dataclass(frozen=True, slots=True)
class CommandEntry:
    id: str
    label: str
    key: str | None
    risky: bool
    enabled: bool


@dataclass(frozen=True, slots=True)
class CommandView:
    entries: tuple[CommandEntry, ...] = ()


def command_view(registry: CommandRegistry) -> Selector[CommandView]:
    """Project the registry into per-snapshot entries (enabled = available)."""

    def project(snapshot: Snapshot) -> CommandView:
        return CommandView(
            entries=tuple(
                CommandEntry(
                    id=c.id,
                    label=c.label,
                    key=c.key,
                    risky=c.risky,
                    enabled=c.available(snapshot),
                )
                for c in registry.commands
            )
        )

    return Selector(project)


# --- Fuzzy matching ----------------------------------------------------------


def match_score(query: str, text: str) -> int | None:
    """Case-insensitive subsequence match score, or None if no match.

    Higher is better: contiguous runs and word-boundary starts score more.
    """
    if not query:
        return 0
    q = query.lower()
    t = text.lower()
    score = 0
    run = 0
    qi = 0
    for i, ch in enumerate(t):
        if qi < len(q) and ch == q[qi]:
            score += 1
            run += 1
            score += run  # contiguity bonus
            if i == 0 or not t[i - 1].isalnum():
                score += 5  # word-boundary bonus
            qi += 1
        else:
            run = 0
    return score if qi == len(q) else None


def filter_commands(entries: Iterable[CommandEntry], query: str) -> tuple[CommandEntry, ...]:
    """Filter+rank entries by id/label match; empty query keeps registry order."""
    ordered = tuple(entries)
    if not query:
        return ordered
    scored: list[tuple[int, int, CommandEntry]] = []
    for order, entry in enumerate(ordered):
        best = max(
            (
                s
                for s in (match_score(query, entry.label), match_score(query, entry.id))
                if s is not None
            ),
            default=None,
        )
        if best is not None:
            scored.append((best, order, entry))
    scored.sort(key=lambda t: (-t[0], t[1]))
    return tuple(entry for _score, _order, entry in scored)
