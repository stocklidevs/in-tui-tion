"""Reducers: pure functions folding events into state slices."""

from __future__ import annotations

from collections.abc import Callable
from types import MappingProxyType
from typing import Any, Protocol

from intui.events.envelope import Event
from intui.state.snapshot import Snapshot

SliceReducer = Callable[[Any, Event], Any]
"""``(slice_state, event) -> new_slice_state``. MUST be pure and MUST return
the state unchanged for unknown event types."""


class Reducer(Protocol):
    """``(snapshot, event) -> snapshot``, with a defined initial snapshot."""

    def __call__(self, snapshot: Snapshot, event: Event) -> Snapshot: ...

    def initial(self) -> Snapshot: ...


class _ComposedReducer:
    """Each slice reducer owns a named slice of the snapshot."""

    def __init__(self, slices: dict[str, tuple[SliceReducer, Any]]) -> None:
        self._reducers = {name: fn for name, (fn, _initial) in slices.items()}
        self._initial_slices = {name: initial for name, (_fn, initial) in slices.items()}

    def initial(self) -> Snapshot:
        return Snapshot(slices=MappingProxyType(dict(self._initial_slices)))

    def __call__(self, snapshot: Snapshot, event: Event) -> Snapshot:
        new_slices = {
            name: fn(snapshot.slices[name], event) for name, fn in self._reducers.items()
        }
        return snapshot.with_slices(new_slices)


def compose_reducers(**slices: tuple[SliceReducer, Any]) -> _ComposedReducer:
    """Compose slice reducers into one Reducer.

    Each keyword maps a slice name to ``(reducer_fn, initial_state)``.
    """
    return _ComposedReducer(dict(slices))
