"""Append-only event stream with dedupe and health tracking."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from intui.events.envelope import Event


class StreamState(Enum):
    LIVE = "live"
    ENDED = "ended"
    DISCONNECTED = "disconnected"
    ERRORING = "erroring"


@dataclass(frozen=True, slots=True)
class StreamError:
    """A reported per-event failure (envelope rejection or reducer error)."""

    event_id: str | None
    reason: str


@dataclass(frozen=True, slots=True)
class StreamHealth:
    """Derived health of the stream's source (FR-007)."""

    state: StreamState = StreamState.LIVE
    last_event_at: datetime | None = None
    rejected_count: int = 0
    duplicate_count: int = 0
    last_error: StreamError | None = None


class EventStream:
    """Ordered, append-only sequence of accepted events.

    Invariants (data-model.md): accepted events are never mutated or removed;
    ``event_id`` is unique — duplicates are silently dropped and counted.
    """

    def __init__(self) -> None:
        self._events: list[Event] = []
        self._seen_ids: set[str] = set()
        self._health = StreamHealth()

    @property
    def events(self) -> tuple[Event, ...]:
        return tuple(self._events)

    @property
    def health(self) -> StreamHealth:
        return self._health

    def append(self, event: Event) -> bool:
        """Append an accepted event. Returns False for duplicates (dropped)."""
        if event.event_id in self._seen_ids:
            self._health = StreamHealth(
                state=self._health.state,
                last_event_at=self._health.last_event_at,
                rejected_count=self._health.rejected_count,
                duplicate_count=self._health.duplicate_count + 1,
                last_error=self._health.last_error,
            )
            return False
        self._events.append(event)
        self._seen_ids.add(event.event_id)
        self._health = StreamHealth(
            state=StreamState.LIVE,
            last_event_at=event.timestamp,
            rejected_count=self._health.rejected_count,
            duplicate_count=self._health.duplicate_count,
            last_error=self._health.last_error,
        )
        return True

    def record_rejection(self, event_id: str | None, reason: str) -> None:
        """Report a per-event failure; the stream and UI continue (FR-008)."""
        self._health = StreamHealth(
            state=StreamState.ERRORING,
            last_event_at=self._health.last_event_at,
            rejected_count=self._health.rejected_count + 1,
            duplicate_count=self._health.duplicate_count,
            last_error=StreamError(event_id=event_id, reason=reason),
        )

    def mark_ended(self) -> None:
        self._set_state(StreamState.ENDED)

    def mark_disconnected(self) -> None:
        self._set_state(StreamState.DISCONNECTED)

    def _set_state(self, state: StreamState) -> None:
        self._health = StreamHealth(
            state=state,
            last_event_at=self._health.last_event_at,
            rejected_count=self._health.rejected_count,
            duplicate_count=self._health.duplicate_count,
            last_error=self._health.last_error,
        )
