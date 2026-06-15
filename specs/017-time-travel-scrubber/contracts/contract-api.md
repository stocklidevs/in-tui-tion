# API Contract: Time-Travel Scrubber

**Feature**: `017-time-travel-scrubber` | **Date**: 2026-06-14

New surface and guarantees tests pin. Additive.

## `Store.snapshot_at` (engine-free)

```python
Store.snapshot_at(index: int) -> Snapshot
```

Guarantees:
- Returns the snapshot after reducing exactly the first `clamp(index, 0,
  len(store.events))` accepted events, from the reducer's initial.
- An event whose reduction raises is skipped (mirrors live isolation), so the
  result matches what live produced at that point.
- Pure: does not mutate the live snapshot or stream; repeatable.
- `snapshot_at(len(store.events))` reduces to the live state.

## `Timeline` (engine-free, `intui.state`)

```python
from intui.state import Timeline
```

Guarantees:
- `Timeline()` is live (`live is True`); `position(total) == total`.
- `step`, `to_start`, `pause` yield a paused timeline; `to_end`, `resume` yield a
  live one; `toggle` flips between freeze-at-total and live.
- `position(total)` is clamped to `[0, total]`; immutable (ops return new
  instances); deterministic.
- `label(total)` describes the mode + position.

## `StoreBridge` — hold / release

Guarantees:
- `hold(snapshot)` renders `snapshot` to all widgets and freezes live flushing
  (live publishes still update the tracked latest).
- `release()` resumes rendering the latest live snapshot immediately.

## `ConsoleApp` — scrubber

Guarantees:
- Scrub keys (`space` pause/resume, `,`/`.` step, `home` start, `end` live) move a
  `Timeline`; while paused, all bound widgets show `snapshot_at(position)`;
  resuming returns to live and follows new events.
- A status bar shows live/paused + `n / total`; the total updates as events arrive
  while paused.
- Scrubbing never mutates the run; scrub keys do not shadow the view keys.

## Backward compatibility

- Purely additive: one `Store` method, a new `Timeline` (exported from
  `intui.state`), two `StoreBridge` methods, and ConsoleApp keys/status. No
  existing signatures change.
