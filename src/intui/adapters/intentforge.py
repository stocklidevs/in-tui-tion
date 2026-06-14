"""IntentForge adapter: normalize IF run-trace ndjson into canonical events.

Engine-free. IntentForge emits ``--event-stream ndjson`` lines of
``{"type":"run_trace_event","event":{"sequence","name","payload"}}`` and a final
``{"type":"summary","summary":{...}}``. The inner record is NOT an intui envelope,
so this module *transforms* each record into one (vs. the plain unwrap that
:class:`~intui.events.NdjsonStreamSource` does). IntentForge is not imported —
the coupling is to its on-the-wire JSON shape only.

Mapping verified against the IF repo 2026-06-14 (run_trace.py, assembly_executor
.py, assembly_benchmark.py, file_diff.py, cli.py). See
specs/010-intentforge-adapter/data-model.md.
"""

from __future__ import annotations

from collections.abc import AsyncIterable, AsyncIterator, Iterable, Mapping, Sequence
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from intui.events.envelope import Event, Scope
from intui.events.sources import _aiter_subprocess_lines, _aiter_text_lines

#: Deterministic time base — IF events carry no timestamp, so we synthesize a
#: monotonic one from the record ``sequence`` to keep replays deterministic.
_EPOCH = datetime(2020, 1, 1, tzinfo=UTC)

#: Summary top-level keys lifted into evidence metrics (present-only).
_SUMMARY_METRIC_KEYS = (
    "case_pass_rate",
    "quality_issue_count",
    "delivered_files",
    "evidence_signature",
)


def adapt_record(record: Mapping[str, Any], *, run_id: str = "intentforge") -> Event | None:
    """Map one IntentForge record to a canonical :class:`Event`, or ``None``.

    Accepts a ``run_trace_event`` wrapper, a bare ``{sequence,name,payload}``, or
    a ``{"type":"summary","summary":{...}}`` record. Never raises on missing keys.
    """
    if record.get("type") == "summary":
        return _adapt_summary(record.get("summary"), run_id=run_id)

    inner = record.get("event") if record.get("type") == "run_trace_event" else record
    if not isinstance(inner, Mapping):
        return None
    name = inner.get("name")
    if not isinstance(name, str):
        return None
    sequence = inner.get("sequence")
    sequence = sequence if isinstance(sequence, int) else 0
    payload = inner.get("payload")
    payload = payload if isinstance(payload, Mapping) else {}

    builder = _MAPPING.get(name)
    if builder is None:
        return None
    type_, scope, out_payload, status = builder(payload)
    return Event(
        version="1",
        event_id=f"if-{sequence}",
        run_id=run_id,
        timestamp=_EPOCH + timedelta(seconds=sequence),
        type=type_,
        scope=scope,
        status=status,
        payload=out_payload,
    )


# --- Per-event builders ------------------------------------------------------
# Each returns (canonical_type, scope, payload, status).

_Built = tuple[str, Scope, dict[str, Any], str | None]


def _item_id(payload: Mapping[str, Any]) -> str:
    # Assembly items carry their id in case_id; file_diff sets work_item_id too.
    wid = payload.get("work_item_id")
    if isinstance(wid, str) and wid:
        return wid
    cid = payload.get("case_id")
    return cid if isinstance(cid, str) else ""


def _case_id(payload: Mapping[str, Any]) -> str:
    cid = payload.get("case_id")
    return cid if isinstance(cid, str) else ""


def _suite_id(payload: Mapping[str, Any]) -> str | None:
    # IF 0.9.13+ carries the parent blueprint/suite as suite_id; absent in older
    # streams (work items then fall back to the kit's "unassigned" group).
    sid = payload.get("suite_id")
    return sid if isinstance(sid, str) and sid else None


def _status(payload: Mapping[str, Any]) -> str | None:
    status = payload.get("status")
    return status if isinstance(status, str) else None


def _case_started(p: Mapping[str, Any]) -> _Built:
    return "task_started", Scope(task_id=_case_id(p)), {}, None


def _case_finished(p: Mapping[str, Any]) -> _Built:
    return "task_completed", Scope(task_id=_case_id(p)), {}, _status(p)


def _item_started(p: Mapping[str, Any]) -> _Built:
    return "work_item_started", Scope(task_id=_suite_id(p), work_item_id=_item_id(p)), {}, None


def _item_committed(p: Mapping[str, Any]) -> _Built:
    return "work_item_completed", Scope(task_id=_suite_id(p), work_item_id=_item_id(p)), {}, None


def _item_failed(p: Mapping[str, Any]) -> _Built:
    return (
        "work_item_completed",
        Scope(task_id=_suite_id(p), work_item_id=_item_id(p)),
        {},
        _status(p) or "failed",
    )


def _plan_blocked(p: Mapping[str, Any]) -> _Built:
    return "task_blocked", Scope(task_id=_case_id(p)), {}, _status(p)


def _suite_started(p: Mapping[str, Any]) -> _Built:
    return "run_started", Scope(), {}, None


def _suite_finished(p: Mapping[str, Any]) -> _Built:
    return "run_completed", Scope(), {}, _status(p)


def _file_diff(p: Mapping[str, Any]) -> _Built:
    diff = p.get("diff")
    title = p.get("file")
    return (
        "diff_ready",
        Scope(task_id=_suite_id(p), work_item_id=_item_id(p)),
        {
            "unified": diff if isinstance(diff, str) else "",
            "title": title if isinstance(title, str) and title else "diff",
            "public_safe": True,
        },
        None,
    )


def _repeat_started(p: Mapping[str, Any]) -> _Built:
    text = f"repeat {p.get('repeat_count', '?')} started (run {p.get('run_index', '?')})"
    return "message_added", Scope(), {"role": "system", "text": text}, None


def _repeat_finished(p: Mapping[str, Any]) -> _Built:
    text = f"repeat {p.get('repeat_count', '?')} finished: {p.get('status', '?')}"
    return "message_added", Scope(), {"role": "system", "text": text}, None


_MAPPING: Mapping[str, Any] = {
    "case_started": _case_started,
    "case_finished": _case_finished,
    "assembly_item_started": _item_started,
    "assembly_item_committed": _item_committed,
    "assembly_item_failed": _item_failed,
    "assembly_plan_blocked": _plan_blocked,
    "matrix_suite_started": _suite_started,
    "matrix_suite_finished": _suite_finished,
    "file_diff": _file_diff,
    "repeat_started": _repeat_started,
    "repeat_finished": _repeat_finished,
}


def _adapt_summary(summary: Any, *, run_id: str) -> Event | None:
    if not isinstance(summary, Mapping):
        return None
    metrics: list[dict[str, Any]] = []
    for key in _SUMMARY_METRIC_KEYS:
        if key in summary:
            metrics.append({"key": key, "label": key.replace("_", " "), "value": summary[key]})
    acb = summary.get("acb_score")
    if isinstance(acb, Mapping) and "certified_level" in acb:
        metrics.append(
            {"key": "certified_level", "label": "certified level", "value": acb["certified_level"]}
        )
    return Event(
        version="1",
        event_id="if-summary",
        run_id=run_id,
        timestamp=_EPOCH + timedelta(days=1),  # after any sequenced event
        type="evidence_ready",
        scope=Scope(),
        payload={"title": "IntentForge summary", "metrics": metrics, "public_safe": True},
    )


class IntentForgeSource:
    """An :class:`EventSource` that adapts an IntentForge ndjson stream.

    Reads raw IF ndjson (a file path, a line iterable, or — via
    :meth:`from_command` — a spawned subprocess) and yields adapted canonical
    envelope mappings, including the trailing summary. Malformed lines surface
    through stream health; unmapped records are skipped.
    """

    def __init__(
        self,
        source: Path | str | Iterable[str] | AsyncIterable[str],
        *,
        run_id: str = "intentforge",
    ) -> None:
        self._source = source
        self._run_id = run_id
        self._cmd: tuple[str, ...] | None = None

    @classmethod
    def from_command(cls, cmd: Sequence[str], *, run_id: str = "intentforge") -> IntentForgeSource:
        """Spawn ``cmd`` and adapt its stdout ndjson live."""
        self = cls([], run_id=run_id)
        self._cmd = tuple(cmd)
        return self

    async def _lines(self) -> AsyncIterator[str]:
        if self._cmd is not None:
            async for line in _aiter_subprocess_lines(self._cmd):
                yield line
        else:
            async for line in _aiter_text_lines(self._source):
                yield line

    async def __aiter__(self) -> AsyncIterator[Mapping[str, Any]]:
        import json

        line_number = 0
        async for line in self._lines():
            line_number += 1
            stripped = line.strip()
            if not stripped:
                continue
            try:
                record: Any = json.loads(stripped)
            except json.JSONDecodeError as exc:
                yield {"__malformed__": f"invalid JSON: {exc}", "line_number": line_number}
                continue
            if not isinstance(record, dict):
                yield {"__malformed__": "line is not a JSON object", "line_number": line_number}
                continue
            event = adapt_record(record, run_id=self._run_id)
            if event is not None:
                yield event.to_mapping()
