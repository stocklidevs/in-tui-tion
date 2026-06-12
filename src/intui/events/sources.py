"""Event sources: async iterators of raw envelope mappings.

Live external sources (process attach, network) are intentionally out of
scope for the foundation, but MUST be implementable against
:class:`EventSource` unchanged.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Iterable, Mapping
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from intui.events.envelope import Event
from intui.events.recording import OnMalformed, iter_recording


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


class JsonlReplaySource:
    """Replay a JSONL recording as an event source (FR-006).

    ``rate`` paces delivery in events/second (None = as fast as possible);
    pacing affects timing only, never outcomes — replay stays deterministic.
    Malformed lines follow ``on_malformed``: ``"skip"`` forwards the raw line
    invalid as-is so the store reports it through health; ``"halt"`` stops
    the source (surfaced as a disconnect).
    """

    def __init__(
        self,
        path: Path | str,
        *,
        rate: float | None = None,
        on_malformed: OnMalformed = "skip",
    ) -> None:
        self._path = Path(path)
        self._delay = None if rate is None else 1.0 / rate
        self._on_malformed: OnMalformed = on_malformed

    async def __aiter__(self) -> AsyncIterator[Mapping[str, Any]]:
        for item in iter_recording(self._path, on_malformed=self._on_malformed):
            if isinstance(item, Event):
                yield item.to_mapping()
            else:
                # Skip mode: surface the failure as an invalid envelope so the
                # store records it in stream health and the run continues.
                yield {"__malformed__": item.reason, "line_number": item.line_number}
            if self._delay is not None:
                await asyncio.sleep(self._delay)
