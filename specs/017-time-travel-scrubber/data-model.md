# Data Model: Time-Travel Scrubber

**Feature**: `017-time-travel-scrubber` | **Date**: 2026-06-14

No new events or slices — a pure reconstruction method, a cursor controller, and
bridge/console wiring.

## `Store.snapshot_at` (engine-free)

```text
Store.snapshot_at(index: int) -> Snapshot
```

- `n = clamp(index, 0, len(self.events))`.
- Fold the reducer over `self.events[:n]` from `reducer.initial()`, skipping any
  event whose reduction raises (mirrors live isolation); attach current health.
- Returns the historical snapshot; does **not** mutate live state.
- `snapshot_at(len(events))` equals the live snapshot's reduced state.

## `Timeline` (engine-free, `intui.state.timeline`)

```text
@dataclass(frozen=True)
Timeline(cursor: int | None = None)        # None = live (follow the end)

  live: bool                               # cursor is None
  position(total: int) -> int              # total if live else clamp(cursor,0,total)
  label(total: int) -> str                 # "live · N events" / "paused n / N"
  toggle(total: int) -> Timeline           # live -> paused@total ; paused -> live
  step(delta: int, total: int) -> Timeline # paused @ clamp(position+delta,0,total)
  to_start() -> Timeline                   # paused @ 0
  to_end() -> Timeline                     # live
  pause(total: int) -> Timeline            # paused @ position
  resume() -> Timeline                     # live
```

Immutable; every op returns a new instance. `step`/`to_start`/`pause` produce a
paused timeline; `to_end`/`resume` produce a live one.

## `StoreBridge` — hold / release

```text
StoreBridge.hold(snapshot: Snapshot) -> None    # render this snapshot; freeze live flush
StoreBridge.release() -> None                    # resume rendering the latest live snapshot
```

- `_held: Snapshot | None`; `_flush`/immediate-render target = `_held or _latest`.
- While `_held` is set, `_on_snapshot` updates `_latest` but does not schedule a
  flush (view frozen).

## `ConsoleApp` — scrubber

- `self._timeline: Timeline` (starts live).
- BINDINGS: `space` `action_scrub_toggle`, `,` `action_scrub_back`, `.`
  `action_scrub_forward`, `home` `action_scrub_start`, `end` `action_scrub_live`.
- `_apply_scrub()`: `total = len(self.store.events)`; if `timeline.live`:
  `bridge.release()`; else `bridge.hold(store.snapshot_at(timeline.position(total)))`;
  update the `#scrub-bar` Static with `timeline.label(total)`.
- Subscribes to the store: on publish, refresh the scrub-bar label (total) — the
  held view stays fixed while paused; live keeps rendering via the bridge.
- A `Static(id="scrub-bar")` rendered above the command bar.

## What does NOT change

- Event envelope, reducers, selectors, widgets, the recording format. Additive:
  one `Store` method, one engine-free `Timeline`, two `StoreBridge` methods, and
  ConsoleApp keys/status — no new state or events.
