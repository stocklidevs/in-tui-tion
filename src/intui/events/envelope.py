"""Versioned event envelope (schema v1).

Contract: specs/001-core-library-foundation/contracts/event-envelope.schema.json
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from types import MappingProxyType
from typing import Any

SUPPORTED_VERSIONS = frozenset({"1"})

_KNOWN_SCOPE_KEYS = ("session_id", "task_id", "work_item_id", "lane_id")
_EMPTY_MAPPING: Mapping[str, Any] = MappingProxyType({})


class EnvelopeError(Exception):
    """An envelope failed validation.

    Carries the offending ``event_id`` when it could be determined, and the
    recording line number when raised by a reader.
    """

    def __init__(
        self,
        reason: str,
        *,
        event_id: str | None = None,
        line_number: int | None = None,
    ) -> None:
        super().__init__(reason)
        self.reason = reason
        self.event_id = event_id
        self.line_number = line_number


@dataclass(frozen=True, slots=True)
class Scope:
    """What an event is about. All fields optional; adapters may add keys."""

    session_id: str | None = None
    task_id: str | None = None
    work_item_id: str | None = None
    lane_id: str | None = None
    extra: Mapping[str, str] = field(default_factory=lambda: _EMPTY_MAPPING)

    def to_mapping(self) -> dict[str, str]:
        out = {k: v for k in _KNOWN_SCOPE_KEYS if (v := getattr(self, k)) is not None}
        out.update(self.extra)
        return out


@dataclass(frozen=True, slots=True)
class Event:
    """An append-only fact in a versioned envelope."""

    version: str
    event_id: str
    run_id: str
    timestamp: datetime
    type: str
    scope: Scope
    status: str | None = None
    summary: str | None = None
    payload: Mapping[str, Any] = field(default_factory=lambda: _EMPTY_MAPPING)

    def to_mapping(self) -> dict[str, Any]:
        """Serialize back to the raw envelope form (lossless round-trip)."""
        out: dict[str, Any] = {
            "version": self.version,
            "event_id": self.event_id,
            "run_id": self.run_id,
            "timestamp": self.timestamp.isoformat().replace("+00:00", "Z"),
            "type": self.type,
            "scope": self.scope.to_mapping(),
        }
        if self.status is not None:
            out["status"] = self.status
        if self.summary is not None:
            out["summary"] = self.summary
        if self.payload:
            out["payload"] = dict(self.payload)
        return out


def _require_str(data: Mapping[str, Any], key: str, event_id: str | None) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value:
        raise EnvelopeError(f"missing or empty required field: {key}", event_id=event_id)
    return value


def parse_event(data: Mapping[str, Any]) -> Event:
    """Validate a raw mapping against envelope schema v1 and build an Event.

    Raises :class:`EnvelopeError` on any validation failure. Unknown *event
    types* are accepted (open vocabulary); unknown *envelope versions* are not.
    """
    event_id = data.get("event_id") if isinstance(data.get("event_id"), str) else None

    version = _require_str(data, "version", event_id)
    if version not in SUPPORTED_VERSIONS:
        raise EnvelopeError(f"unsupported envelope version: {version!r}", event_id=event_id)

    event_id = _require_str(data, "event_id", event_id)
    run_id = _require_str(data, "run_id", event_id)
    raw_timestamp = data.get("timestamp")
    if not isinstance(raw_timestamp, str) or not raw_timestamp:
        raise EnvelopeError("missing or empty required field: timestamp", event_id=event_id)
    try:
        timestamp = datetime.fromisoformat(raw_timestamp.replace("Z", "+00:00"))
    except ValueError as exc:
        raise EnvelopeError(f"unparseable timestamp: {raw_timestamp!r}", event_id=event_id) from exc
    type_ = _require_str(data, "type", event_id)

    raw_scope = data.get("scope")
    if not isinstance(raw_scope, Mapping):
        raise EnvelopeError("missing or invalid required field: scope", event_id=event_id)
    known = {k: v for k, v in raw_scope.items() if k in _KNOWN_SCOPE_KEYS}
    extra = {k: str(v) for k, v in raw_scope.items() if k not in _KNOWN_SCOPE_KEYS}
    scope = Scope(**known, extra=MappingProxyType(extra))

    status = data.get("status")
    summary = data.get("summary")
    payload = data.get("payload", _EMPTY_MAPPING)
    if not isinstance(payload, Mapping):
        raise EnvelopeError("payload must be a mapping", event_id=event_id)

    return Event(
        version=version,
        event_id=event_id,
        run_id=run_id,
        timestamp=timestamp,
        type=type_,
        scope=scope,
        status=status if isinstance(status, str) else None,
        summary=summary if isinstance(summary, str) else None,
        payload=MappingProxyType(dict(payload)),
    )
