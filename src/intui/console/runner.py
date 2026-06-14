"""watch(): the one-line front door to the zero-config console."""

from __future__ import annotations

from pathlib import Path

from intui.console.app import ConsoleApp, build_console
from intui.events import EventSource, NdjsonStreamSource

#: Record types unwrapped by default — matches real producer output
#: (e.g. IntentForge's ``{"type":"run_trace_event","event":{...}}``).
DEFAULT_RECORD_TYPES = ("run_trace_event",)


def _as_source(source: EventSource | Path | str, *, rate: float | None) -> EventSource:
    if isinstance(source, (Path, str)):
        return NdjsonStreamSource(source, event_record_types=DEFAULT_RECORD_TYPES, rate=rate)
    return source


def watch(
    source: EventSource | Path | str,
    *,
    public_safe: bool = True,
    rate: float | None = None,
) -> None:
    """Render a console from a stream file path or any :class:`EventSource`.

    A path is replayed as ndjson (wrapped records unwrapped, non-event records
    ignored); an :class:`EventSource` is used directly. Public-safe by default.
    """
    app = build_app(source, public_safe=public_safe, rate=rate)
    app.run()


def build_app(
    source: EventSource | Path | str,
    *,
    public_safe: bool = True,
    rate: float | None = None,
) -> ConsoleApp:
    """Build (but do not run) the console — the testable core of :func:`watch`."""
    return build_console(_as_source(source, rate=rate), public_safe=public_safe)
