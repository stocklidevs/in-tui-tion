# Research & Decisions: Time-Travel Scrubber

**Feature**: `017-time-travel-scrubber` | **Date**: 2026-06-14

## D1 — Reconstruct via `Store.snapshot_at(n)` (re-reduce the prefix)

**Decision**: Add `Store.snapshot_at(n)` that folds the reducer over the first `n`
accepted events from `reducer.initial()`, returning the resulting snapshot
(health attached). It reads `self._stream.events` + `self._reducer`; it does not
touch the live snapshot.

**Why**: The reducer is pure and the event log is retained, so any past state is
`reduce(events[:n])` — exact, deterministic, and free of extra storage. Putting it
on the `Store` reuses the reducer it already holds and keeps the capability
engine-free and core.

**Alternatives rejected**: snapshotting state on every ingest (memory + couples
the store to time-travel); an external replay store (duplicates the reducer/log).

## D2 — Mirror live per-event isolation during reconstruction

**Decision**: Wrap each reduce in `try/except` and skip on failure — exactly what
live ingest does (it records a rejection and keeps the prior snapshot).

**Why**: A reconstructed snapshot must equal what live produced; if a malformed/
failing event left live state unchanged, reconstruction must too. (Note: events
whose reduction raised are still in the retained log, so they must be skipped, not
re-raised.)

**Alternatives rejected**: re-raise on failure — diverges from live state and
crashes the scrubber.

## D3 — `Timeline`: cursor is `int | None` (None = live)

**Decision**: An immutable `Timeline(cursor: int | None = None)`; `None` means
"follow the end" (live). `position(total)` returns `total` when live, else the
clamped cursor. Ops: `toggle(total)` (live→freeze at total / paused→live),
`step(±1, total)`, `to_start()` (0), `to_end()` (live), plus `live` and
`label(total)`. Operations return new instances.

**Why**: A single nullable cursor cleanly distinguishes "following live" from "at
a fixed point," makes clamping a pure function of the current total (which grows
on a live stream), and keeps the controller tiny and deterministic.

**Alternatives rejected**: separate `playing` bool + index — redundant state to
keep consistent; storing `total` inside the Timeline — couples it to a moving
value better passed in at call time.

## D4 — Bridge `hold`/`release` to render a held snapshot

**Decision**: `StoreBridge` gains `_held: Snapshot | None`; `hold(snap)` sets it
and renders it now; `release()` clears it and renders `_latest`. While held,
`_on_snapshot` keeps updating `_latest` (so resume is instant) but does **not**
flush; `_flush` renders `_held or _latest`.

**Why**: Pausing must freeze the view while ingestion continues; tracking
`_latest` underneath means `release()` shows the up-to-date live state with no
re-subscribe. Minimal change to the existing coalescing flush.

**Alternatives rejected**: unsubscribe/resubscribe on pause — loses buffered
updates and is racy; push historical snapshots through `store.subscribe` — would
fight live publishes.

## D5 — Scrub keys chosen to avoid collisions

**Decision**: `space` = pause/resume(toggle), `,` = step back, `.` = step
forward, `home` = jump to start, `end` = resume to live. App-level bindings.

**Why**: `,`/`.` are the conventional frame-step keys and don't collide with the
console view keys (t/l/f/d/e/m/p) or with arrow-key widget navigation (so a
focused Tree/list still uses arrows). `space` is the universal play/pause.

**Alternatives rejected**: arrow keys for stepping — collide with focused-widget
navigation; `p` — already the palette key.

## D6 — A status bar, not a draggable timeline widget

**Decision**: Show a one-line status (`▶ live · N events` / `⏸ n / total`) above
the command bar; update it on each scrub key and on store publishes (so the total
climbs while paused). No graphical/draggable timeline in v1.

**Why**: The status line delivers the needed feedback (mode + position) cheaply
and keyboard-first; a draggable timeline (mouse) is a nice-to-have that can come
later.

**Alternatives rejected**: a full timeline scrollbar widget — more surface than
the milestone needs; no indicator — the user can't tell they're paused/where.

## D7 — Console subscription keeps the status fresh while paused

**Decision**: `ConsoleApp` subscribes to the store; on each publish it refreshes
the status bar (total) and, when paused, leaves the held snapshot fixed; when
live it does nothing extra (the bridge already renders live).

**Why**: While paused on a growing stream, the total must climb even though the
view is frozen (FR-007). A lightweight subscription updates only the indicator.

**Alternatives rejected**: poll on a timer — wasteful; bake the indicator into a
bound widget — it must reflect *total*, not the held snapshot.

## Open questions / deferred

- **Checkpointing** for very large histories (snapshot every K events to bound
  re-reduction cost) — future optimization.
- **Draggable/mouse timeline** widget — future.
- **Jump-to-event-of-interest** (next failure, next diff) — future nicety.
