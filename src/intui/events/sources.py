"""Event sources: async iterators of raw envelope mappings.

Live external sources (process attach, network) are intentionally out of
scope for the foundation, but MUST be implementable against
:class:`EventSource` unchanged.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterable, Mapping
from typing import Any, Protocol, runtime_checkable

from intui.events.envelope import Event


@runtime_checkable
class EventSource(Protocol):
    """Async iterator of raw envelope mappings."""

    def __aiter__(self) -> AsyncIterator[Mapping[str, Any]]: ...


class MemorySource:
    """In-memory source over a finite sequence (tests, scripted demos)."""

    def __init__(self, events: Iterable[Event | Mapping[str, Any]]) -> None:
        self._items: list[Event | Mapping[str, Any]] = list(events)

    async def __aiter__(self) -> AsyncIterator[Mapping[str, Any]]:
        items, self._items = self._items, []
        for item in items:
            yield item.to_mapping() if isinstance(item, Event) else item
