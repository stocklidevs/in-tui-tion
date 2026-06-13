"""JSONL recordings: lossless write/read of event streams (FR-006).

Format: one envelope object per line, UTF-8 (contract R4 in research.md).
Recordings are streamable, diffable, and human-inspectable.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import Any, Literal

from intui.events.envelope import EnvelopeError, Event, parse_event

OnMalformed = Literal["skip", "halt"]


def write_recording(path: Path | str, events: Iterable[Event]) -> None:
    """Write events as JSON Lines. Round-trips losslessly via read_recording."""
    with Path(path).open("w", encoding="utf-8", newline="\n") as f:
        for event in events:
            json.dump(event.to_mapping(), f, ensure_ascii=False)
            f.write("\n")


def iter_recording(
    path: Path | str, *, on_malformed: OnMalformed = "skip"
) -> Iterator[Event | EnvelopeError]:
    """Yield parsed events; malformed lines yield (skip) or raise (halt) an
    EnvelopeError carrying the line number and reason."""
    with Path(path).open("r", encoding="utf-8") as f:
        for line_number, line in enumerate(f, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                data: Any = json.loads(stripped)
                if not isinstance(data, dict):
                    raise EnvelopeError("line is not a JSON object", line_number=line_number)
                yield parse_event(data)
            except EnvelopeError as exc:
                error = EnvelopeError(exc.reason, event_id=exc.event_id, line_number=line_number)
                if on_malformed == "halt":
                    raise error from exc
                yield error
            except json.JSONDecodeError as exc:
                error = EnvelopeError(f"invalid JSON: {exc}", line_number=line_number)
                if on_malformed == "halt":
                    raise error from exc
                yield error


def read_recording(path: Path | str, *, on_malformed: OnMalformed = "skip") -> list[Event]:
    """Read a recording into a list of events.

    With ``on_malformed="skip"`` bad lines are dropped; with ``"halt"`` the
    first bad line raises :class:`EnvelopeError` with its line number.
    """
    return [
        item for item in iter_recording(path, on_malformed=on_malformed) if isinstance(item, Event)
    ]
