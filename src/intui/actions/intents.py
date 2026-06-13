"""Intents: named, validated user-triggered requests (Principle III).

The application's :class:`IntentHandler` is the sole mutation seam — the
library delivers intents and never mutates application state itself
(FR-014). Handlers typically respond by appending new events, which flow
back through the pipeline.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Protocol

_EMPTY_PAYLOAD: Mapping[str, Any] = MappingProxyType({})


@dataclass(frozen=True, slots=True)
class Intent:
    """A named user-triggered request.

    ``risky=True`` intents are held by the confirmation flow until the user
    explicitly confirms (FR-016).
    """

    name: str
    payload: Mapping[str, Any] = field(default_factory=lambda: _EMPTY_PAYLOAD)
    risky: bool = False

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Intent):
            return NotImplemented
        return (
            self.name == other.name
            and dict(self.payload) == dict(other.payload)
            and self.risky == other.risky
        )


class IntentHandler(Protocol):
    """The application seam: receives confirmed intents asynchronously."""

    async def __call__(self, intent: Intent) -> None: ...
