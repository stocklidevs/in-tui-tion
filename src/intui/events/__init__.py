"""intui.events: versioned envelopes, append-only streams, and sources."""

from intui.events.envelope import EnvelopeError, Event, Scope, parse_event
from intui.events.sources import EventSource, MemorySource
from intui.events.stream import EventStream, StreamError, StreamHealth, StreamState

__all__ = [
    "EnvelopeError",
    "Event",
    "EventSource",
    "EventStream",
    "MemorySource",
    "Scope",
    "StreamError",
    "StreamHealth",
    "StreamState",
    "parse_event",
]
