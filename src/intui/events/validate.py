"""Stream validator: check a JSONL event stream against the contract.

Engine-free. Envelope problems (reusing ``parse_event``) are hard errors;
event types outside a supplied known-type vocabulary are warnings, matching the
runtime reducer contract (unknown types pass through). A producer can run this
to self-check a stream before pointing a console at it.
"""

from __future__ import annotations

import json
from collections.abc import Collection, Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from intui.events.envelope import EnvelopeError, parse_event


@dataclass(frozen=True, slots=True)
class StreamIssue:
    line: int
    severity: str  # "error" | "warning"
    reason: str
    event_id: str | None = None


def validate_event(
    data: Mapping[str, Any],
    *,
    known_types: Collection[str] | None = None,
    line: int = 0,
) -> list[StreamIssue]:
    """Validate one event mapping; returns issues (empty == valid)."""
    issues: list[StreamIssue] = []
    try:
        event = parse_event(data)
    except EnvelopeError as exc:
        return [StreamIssue(line=line, severity="error", reason=exc.reason, event_id=exc.event_id)]
    if known_types is not None and event.type not in known_types:
        issues.append(
            StreamIssue(
                line=line,
                severity="warning",
                reason=f"unknown event type {event.type!r} (not in the canonical vocabulary)",
                event_id=event.event_id,
            )
        )
    return issues


def validate_stream(
    lines: Iterable[str] | Path | str,
    *,
    known_types: Collection[str] | None = None,
    event_record_types: tuple[str, ...] = (),
) -> list[StreamIssue]:
    """Validate a JSONL stream line-by-line.

    ``lines`` may be an iterable of lines, or a path to a ``.jsonl`` file.
    Blank lines are skipped. If ``event_record_types`` is given, each line is a
    wrapper record ``{"type": <record-type>, "event": {...envelope...}}``; only
    records whose type is in ``event_record_types`` are validated as events,
    others are ignored (e.g. a producer's trailing summary line).
    """
    issues: list[StreamIssue] = []
    for line_no, raw in _iter_lines(lines):
        stripped = raw.strip()
        if not stripped:
            continue
        try:
            record: Any = json.loads(stripped)
        except json.JSONDecodeError as exc:
            issues.append(
                StreamIssue(line=line_no, severity="error", reason=f"invalid JSON: {exc}")
            )
            continue
        if not isinstance(record, dict):
            issues.append(
                StreamIssue(line=line_no, severity="error", reason="line is not a JSON object")
            )
            continue
        event = _unwrap(record, event_record_types)
        if event is None:
            continue  # ignored non-event record
        if not isinstance(event, dict):
            issues.append(
                StreamIssue(line=line_no, severity="error", reason="event is not a JSON object")
            )
            continue
        issues.extend(validate_event(event, known_types=known_types, line=line_no))
    return issues


def _unwrap(record: dict[str, Any], event_record_types: tuple[str, ...]) -> Any:
    if not event_record_types:
        return record
    if record.get("type") in event_record_types:
        return record.get("event")
    return None


def _iter_lines(lines: Iterable[str] | Path | str) -> Iterable[tuple[int, str]]:
    if isinstance(lines, (Path, str)):
        with Path(lines).open("r", encoding="utf-8") as f:
            yield from enumerate(f, start=1)
    else:
        yield from enumerate(lines, start=1)
