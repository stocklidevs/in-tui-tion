"""The Store: the only stateful pipeline object."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from intui.events.envelope import EnvelopeError, Event, parse_event
from intui.events.stream import EventStream
from intui.state.reducer import Reducer
from intui.state.snapshot import Snapshot

Unsubscribe = Callable[[], None]
Subscriber = Callable[[Snapshot], None]


class Store:
    """Holds the current snapshot; ingests events; publishes changes.

    Engine-agnostic and synchronous — the terminal bridge subscribes like any
    other consumer (Principle I).
    """

    def __init__(self, reducer: Reducer, initial: Snapshot | None = None) -> None:
        self._reducer = reducer
        self._stream = EventStream()
        self._snapshot = (initial if initial is not None else reducer.initial()).with_health(
            self._stream.health
        )
        self._subscribers: list[Subscriber] = []

    @property
    def snapshot(self) -> Snapshot:
        return self._snapshot

    @property
    def events(self) -> tuple[Event, ...]:
        """The accepted events, in order (read-only) — e.g. to record a run."""
        return self._stream.events

    def snapshot_at(self, index: int) -> Snapshot:
        """Reconstruct the snapshot after the first ``index`` accepted events.

        Pure time-travel: folds the reducer over ``events[:index]`` from its
        initial state, mirroring live per-event isolation (an event whose
        reduction raises is skipped, as it was live). Clamped to
        ``[0, len(events)]``. Does NOT mutate the live snapshot or stream.
        """
        events = self._stream.events
        n = max(0, min(index, len(events)))
        snapshot = self._reducer.initial()
        for event in events[:n]:
            try:
                snapshot = self._reducer(snapshot, event)
            except Exception:  # noqa: BLE001 - same isolation boundary as ingest
                continue
        return snapshot.with_health(self._stream.health)

    def subscribe(self, callback: Subscriber) -> Unsubscribe:
        self._subscribers.append(callback)

        def unsubscribe() -> None:
            if callback in self._subscribers:
                self._subscribers.remove(callback)

        return unsubscribe

    def ingest(self, event: Event) -> None:
        """Validate ordering invariants, dedupe, reduce, publish.

        Reducer failures are isolated (FR-008): the event is reported through
        stream health and the prior snapshot is retained.
        """
        if not self._stream.append(event):
            return  # duplicate event_id: dropped, not re-reduced
        try:
            reduced = self._reducer(self._snapshot, event)
        except Exception as exc:  # noqa: BLE001 - isolation boundary by design
            self._stream.record_rejection(event.event_id, repr(exc))
            self._snapshot = self._snapshot.with_health(self._stream.health)
        else:
            self._snapshot = reduced.with_health(self._stream.health)
        self._publish()

    def ingest_raw(self, raw: Mapping[str, Any]) -> None:
        """Parse and ingest a raw envelope mapping.

        Envelope validation failures are isolated the same way reducer
        failures are: reported through stream health, never raised.
        """
        try:
            event = parse_event(raw)
        except EnvelopeError as exc:
            self._stream.record_rejection(exc.event_id, exc.reason)
            self._snapshot = self._snapshot.with_health(self._stream.health)
            self._publish()
        else:
            self.ingest(event)

    def mark_ended(self) -> None:
        """Record that the source reached its natural end."""
        self._stream.mark_ended()
        self._snapshot = self._snapshot.with_health(self._stream.health)
        self._publish()

    async def run(self, source: Any) -> Any:
        """Drive a source to completion; never raises for per-event failures.

        Returns the terminal :class:`~intui.events.stream.StreamHealth`:
        ``ENDED`` when the source completes naturally, ``DISCONNECTED`` when
        it fails mid-stream.
        """
        try:
            async for raw in source:
                self.ingest_raw(raw)
        except Exception:
            self.mark_disconnected()
        else:
            self.mark_ended()
        return self._snapshot.health

    def mark_disconnected(self) -> None:
        """Record that the source was lost before its natural end."""
        self._stream.mark_disconnected()
        self._snapshot = self._snapshot.with_health(self._stream.health)
        self._publish()

    def _publish(self) -> None:
        for subscriber in list(self._subscribers):
            subscriber(self._snapshot)
