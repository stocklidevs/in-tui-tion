"""Mode model: current mode reduced from events, switched via intent.

Engine-free. Modes are an ordered named set with one active member, reduced
from ``mode_changed`` events; switching is a ``switch_mode`` intent that the
application turns into a ``mode_changed`` event (intent → event → state,
Principle III).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Any

from intui.actions.intents import Intent
from intui.events.envelope import Event
from intui.state.snapshot import Snapshot
from intui.viewmodels.selector import Selector

#: Canonical event types the mode reducer consumes (stream contract).
MODE_EVENT_TYPES = frozenset({"mode_changed"})


@dataclass(frozen=True, slots=True)
class ModeState:
    modes: tuple[str, ...]
    current: str


@dataclass(frozen=True, slots=True)
class ModeEntry:
    name: str
    active: bool


@dataclass(frozen=True, slots=True)
class ModeView:
    entries: tuple[ModeEntry, ...] = ()


def mode_slice(modes: Sequence[str], initial: str | None = None) -> tuple[Any, ModeState]:
    """``(reducer, initial)`` for ``compose_reducers(modes=mode_slice(...))``."""
    ordered = tuple(modes)
    current = initial if initial in ordered else (ordered[0] if ordered else "")

    def reduce(state: ModeState, event: Event) -> ModeState:
        if event.type == "mode_changed":
            target = event.payload.get("mode")
            if isinstance(target, str) and target in state.modes and target != state.current:
                return replace(state, current=target)
        return state

    return reduce, ModeState(modes=ordered, current=current)


def mode_view(slice_name: str = "modes") -> Selector[ModeView]:
    def project(snapshot: Snapshot) -> ModeView:
        state: ModeState = snapshot.slice(slice_name)
        return ModeView(
            entries=tuple(ModeEntry(name=m, active=m == state.current) for m in state.modes)
        )

    return Selector(project)


def switch_mode_intent(mode: str) -> Intent:
    """Build the intent that requests switching to ``mode``."""
    return Intent("switch_mode", {"mode": mode})
