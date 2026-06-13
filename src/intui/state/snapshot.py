"""Immutable application state snapshots."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from types import MappingProxyType
from typing import Any

from intui.events.stream import StreamHealth

_EMPTY_SLICES: Mapping[str, Any] = MappingProxyType({})


class ReducerError(Exception):
    """A reducer raised while folding an event.

    The store isolates the failure: it is reported through stream health and
    the prior snapshot is retained (FR-008).
    """

    def __init__(self, reason: str, *, event_id: str) -> None:
        super().__init__(reason)
        self.reason = reason
        self.event_id = event_id


@dataclass(frozen=True, slots=True)
class Snapshot:
    """Application state at a point in the stream.

    Structural equality: identical event sequences produce equal snapshots
    (FR-003, SC-002).
    """

    state_version: int = 0
    health: StreamHealth = field(default_factory=StreamHealth)
    slices: Mapping[str, Any] = field(default_factory=lambda: _EMPTY_SLICES)

    def slice(self, name: str) -> Any:
        """Return a named state slice. Raises KeyError for unknown names."""
        return self.slices[name]

    def with_slices(self, slices: Mapping[str, Any]) -> Snapshot:
        return replace(
            self, state_version=self.state_version + 1, slices=MappingProxyType(dict(slices))
        )

    def with_health(self, health: StreamHealth) -> Snapshot:
        return replace(self, health=health)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Snapshot):
            return NotImplemented
        return (
            self.state_version == other.state_version
            and self.health == other.health
            and dict(self.slices) == dict(other.slices)
        )
