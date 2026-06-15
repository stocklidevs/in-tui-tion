"""Event sources: async iterators of raw envelope mappings.

Live external sources (process attach, network) are intentionally out of
scope for the foundation, but MUST be implementable against
:class:`EventSource` unchanged.
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterable, AsyncIterator, Iterable, Mapping, Sequence
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


def _decode_ndjson_line(
    line: str, line_number: int, event_record_types: tuple[str, ...]
) -> Mapping[str, Any] | None:
    """Decode one ndjson line into a raw envelope mapping.

    Returns ``None`` for a blank line or an ignored non-event record. Invalid
    JSON / non-objects yield a ``__malformed__`` marker so the store reports
    them through stream health (the run continues). Liberal in what it accepts:
    a wrapped record (``{"type": R, "event": {...}}`` with ``R`` in
    ``event_record_types``) is unwrapped; a bare envelope passes through; any
    other record (e.g. a trailing ``summary``) is ignored.
    """
    stripped = line.strip()
    if not stripped:
        return None
    try:
        record: Any = json.loads(stripped)
    except json.JSONDecodeError as exc:
        return {"__malformed__": f"invalid JSON: {exc}", "line_number": line_number}
    if not isinstance(record, dict):
        return {"__malformed__": "line is not a JSON object", "line_number": line_number}
    inner = record.get("event")
    if isinstance(inner, dict) and (
        not event_record_types or record.get("type") in event_record_types
    ):
        return inner
    if "event_id" in record and "type" in record:
        return record  # a bare envelope
    return None  # a non-event record (e.g. a summary) — ignored


async def _aiter_text_lines(
    lines: Path | str | Iterable[str] | AsyncIterable[str],
) -> AsyncIterator[str]:
    """Yield text lines from a file path, a sync iterable, or an async iterable."""
    if isinstance(lines, (Path, str)):
        with Path(lines).open("r", encoding="utf-8") as f:
            for line in f:
                yield line
    elif isinstance(lines, AsyncIterable):
        async for line in lines:
            yield line
    else:
        for line in lines:
            yield line


async def _aiter_followed_lines(path: Path | str, poll_interval: float) -> AsyncIterator[str]:
    """Tail a file: yield existing lines, then keep yielding appended ones.

    A line appended without its trailing newline is buffered until the newline
    arrives, so it is yielded exactly once. Never ends (the stream stays live);
    closes the handle when the consuming task is cancelled.
    """
    with Path(path).open("r", encoding="utf-8") as f:
        buffer = ""
        while True:
            chunk = f.readline()
            if not chunk:
                await asyncio.sleep(poll_interval)
                continue
            buffer += chunk
            if buffer.endswith("\n"):
                yield buffer
                buffer = ""


class NdjsonStreamSource:
    """An :class:`EventSource` over newline-delimited JSON.

    ``lines`` may be a ``.jsonl`` path, a sync iterable of text lines, or an
    async iterable of text lines (e.g. a live pipe). Wrapped records whose
    ``type`` is in ``event_record_types`` are unwrapped; bare envelopes pass
    through; other records are ignored. Malformed lines are surfaced through
    stream health rather than raised. ``rate`` paces delivery in events/second
    (None = as fast as possible) for finite inputs.
    """

    def __init__(
        self,
        lines: Path | str | Iterable[str] | AsyncIterable[str],
        *,
        event_record_types: tuple[str, ...] = (),
        rate: float | None = None,
        follow: bool = False,
        poll_interval: float = 0.25,
    ) -> None:
        self._lines = lines
        self._event_record_types = event_record_types
        self._delay = None if rate is None else 1.0 / rate
        # Follow (tail) only applies to a file path; other inputs are finite.
        self._follow = follow and isinstance(lines, (Path, str))
        self._poll_interval = poll_interval

    async def __aiter__(self) -> AsyncIterator[Mapping[str, Any]]:
        if self._follow:
            source = _aiter_followed_lines(self._lines, self._poll_interval)  # type: ignore[arg-type]
        else:
            source = _aiter_text_lines(self._lines)
        line_number = 0
        async for line in source:
            line_number += 1
            decoded = _decode_ndjson_line(line, line_number, self._event_record_types)
            if decoded is None:
                continue
            yield decoded
            if self._delay is not None:
                await asyncio.sleep(self._delay)


class SubprocessSource:
    """An :class:`EventSource` that spawns a command and reads its stdout ndjson.

    The command is launched with no shell (``cmd`` is argv). Each stdout line is
    decoded like :class:`NdjsonStreamSource` (unwrapping ``event_record_types``,
    ignoring non-event records). Child stdout EOF ends the stream naturally; a
    spawn failure raises out of iteration (the store marks it disconnected). The
    parent's stdin is never read, so a hosting TUI keeps the keyboard.
    """

    def __init__(
        self,
        cmd: Sequence[str],
        *,
        event_record_types: tuple[str, ...] = (),
    ) -> None:
        self._cmd = tuple(cmd)
        self._event_record_types = event_record_types

    async def __aiter__(self) -> AsyncIterator[Mapping[str, Any]]:
        line_number = 0
        async for line in _aiter_subprocess_lines(self._cmd):
            line_number += 1
            decoded = _decode_ndjson_line(line, line_number, self._event_record_types)
            if decoded is not None:
                yield decoded


async def _aiter_subprocess_lines(cmd: Sequence[str]) -> AsyncIterator[str]:
    """Spawn ``cmd`` (no shell) and yield its stdout lines as text.

    Shared by :class:`SubprocessSource` and the IntentForge adapter source.
    Child stdout EOF ends iteration naturally; a spawn failure raises out of the
    generator (callers surface it as a disconnect). The parent's stdin is never
    read, so a hosting TUI keeps the keyboard.
    """
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdin=asyncio.subprocess.DEVNULL,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.DEVNULL,
    )
    assert process.stdout is not None
    try:
        async for raw in process.stdout:
            yield raw.decode("utf-8", "replace")
    finally:
        if process.returncode is None:
            await process.wait()
