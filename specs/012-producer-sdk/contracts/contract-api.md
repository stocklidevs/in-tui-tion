# API Contract: Producer SDK (emit)

**Feature**: `012-producer-sdk` | **Date**: 2026-06-14

New public surface in `intui.emit`, re-exported from the `intui` root.

## Factory

```python
from intui import run_recorder            # also: from intui.emit import run_recorder, RunRecorder

run_recorder(
    sink: Path | str | TextIO | Callable[[Mapping[str, Any]], None] | None = None,
    *, run_id: str | None = None, clock: Callable[[], datetime] | None = None,
) -> RunRecorder
```

Guarantees:
- Returns a recorder that emits **bare, valid canonical envelopes** — every event
  validates against `KNOWN_EVENT_TYPES` with zero envelope errors.
- `sink=None` → flushed ndjson on stdout; path → flushed ndjson file (closed on
  recorder close); text file → flushed ndjson (not closed); callable → receives
  each envelope mapping.
- `event_id` is a unique, ordered per-recorder counter; `run_id` defaults to a
  generated id; `clock` is injectable (deterministic tests).

## RunRecorder methods

Guarantees (each returns the emitted `Event`):
- `emit(type, *, task_id=…, work_item_id=…, lane_id=…, session_id=…, status=…,
  summary=…, **payload)` — generic; supports any (incl. custom) type.
- Vocabulary helpers per data-model.md emit the matching canonical type with the
  right scope/payload.
- `diff(path, *, before, after, public_safe=True)` emits `diff_ready` whose
  `unified` text `parse_unified_diff` parses into the changed file(s); identical
  before/after yields a no-change diff (no crash).
- `evidence(*, title="evidence", public_safe=True, **metrics)` emits
  `evidence_ready` with `[{key,label,value}]` (label = key with `_`→space).
- Emitting after a file sink is closed raises a clear error (not silent corruption).

## Context managers

Guarantees:
- `with run_recorder(...) as rec:` closes a file sink on exit.
- `with rec.run():` → `run_started` on enter; `run_completed` on normal exit,
  `run_failed` if the block raises (then re-raise).
- `with rec.task(id, title?) as t:` → `task_started` on enter; `task_completed`
  (`status` completed) on normal exit, `status: failed` if it raises (re-raise).
- `with t.work_item(id, …):` → `work_item_started`/`work_item_completed`, scoped
  to the task (`scope.task_id` set), `failed` on raise.

## Cross-cutting

- `intui.emit` imports no terminal engine; `from intui import run_recorder`
  works and the root import stays engine-free (layering guard).
- Output is consumed by `intui watch <file>` and `intui watch -- <tool>` with
  **no adapter** (bare canonical envelopes).

## Backward compatibility

- Purely additive: a new module + root re-exports. No existing symbol changes.
