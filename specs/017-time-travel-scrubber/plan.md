# Implementation Plan: Time-Travel Scrubber

**Branch**: `017-time-travel-scrubber` | **Date**: 2026-06-14 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/017-time-travel-scrubber/spec.md`

## Summary

Pause/step/rewind/resume a run, exploiting the event-sourced core:

1. **`Store.snapshot_at(n)`** (engine-free): reduce the first `n` accepted events
   from the reducer's initial, mirroring live per-event isolation (skip an event
   whose reduction raises), attaching current health. Clamped to `[0, len]`.
   Does not mutate live state.
2. **`Timeline`** (engine-free, `intui.state.timeline`): an immutable cursor —
   `cursor: int | None` (None = live/follow-end) — with `toggle(total)`,
   `step(delta, total)`, `to_start()`, `to_end()`, `position(total)` (clamped),
   `live`, and `label(total)`. Pure, unit-tested.
3. **Bridge hold/release** (`StoreBridge`): render a *held* snapshot (historical)
   while paused; live publishes keep updating `_latest` but don't flush; `release`
   resumes live rendering. So resume is immediate and ingestion never stops.
4. **Console scrubber** (`ConsoleApp`): scrub keys (`space` pause/resume, `,`/`.`
   step, `home` start, `end` live), a status bar (`▶ live · N` / `⏸ n / total`),
   and a store subscription that keeps the status total fresh while paused.

Decisions in [research.md](research.md); shapes in [data-model.md](data-model.md);
surface in [contracts/contract-api.md](contracts/contract-api.md).

## Technical Context

**Language/Version**: Python 3.11–3.13 (unchanged).

**Primary Dependencies**: Textual 6.x (console keys + status bar). No new deps.

**Storage**: n/a (operates over the store's retained events).

**Testing**: pytest headless for `snapshot_at` (equals reduce-first-k, incl. a
reducer that raises on one event → isolation) and `Timeline` (positions, clamp,
toggle, start/end); Pilot for the console scrubber (pause+step shows historical
state; resume returns to live; paused while a live source grows → held view fixed,
status total climbs).

**Target Platform**: unchanged.

**Project Type**: library + examples gallery (unchanged).

**Performance Goals**: `snapshot_at` is O(n) per call (re-reduce); fine for
typical runs. Checkpointing for very large histories is a noted future
optimization (out of scope).

**Constraints**: `snapshot_at` + `Timeline` engine-free (layering guard) and pure
(no live mutation; deterministic); scrubbing never alters the run; scrub keys must
not shadow focused-widget navigation.

**Scale/Scope**: one `Store` method + one engine-free `Timeline` + bridge
hold/release + console keys/status + docs. Out of scope: a draggable timeline
widget, checkpoint caching, editing/branching history, scrubbing the source
itself (we scrub retained events).

## Constitution Check

| # | Principle | Status | Notes |
|---|-----------|--------|-------|
| I | Structured State | ✅ PASS | Historical state is just a reduction of the log; nothing new stored. |
| II | Layered Architecture | ✅ PASS | `snapshot_at` + `Timeline` engine-free; only the bridge + ConsoleApp touch Textual. |
| III | Actions Are Intents | ✅ PASS | Scrubbing is read-only inspection; never mutates the run/stream. |
| IV | Keyboard-First | ✅ PASS | Scrub keys + a visible status bar; non-collide with view/nav keys. |
| V | Meaningful Motion | ✅ PASS | The status bar conveys live vs paused + position. |
| VI | Public-Safe | ✅ PASS | Reconstructed snapshots redact via the same selectors; no new exposure. |
| VII | Test-First, Replayable | ✅ PASS | Reconstruction is the essence of replay; `snapshot_at`/`Timeline` headless test-first. |
| VIII | Example-Driven | ✅ PASS | Documented in quickstart/README; works in the zero-config console. |
| — | New deps justified | ✅ PASS | None. |

**Post-Phase-1 re-check (2026-06-14)**: no new deps; layering holds. GATE: PASS —
Complexity Tracking empty.

## Project Structure

```text
src/intui/state/
├── store.py        # + snapshot_at(n)
├── timeline.py     # NEW — Timeline (engine-free cursor controller)
└── __init__.py     # export Timeline
src/intui/widgets/bridge.py   # + hold(snapshot) / release() / held rendering
src/intui/console/app.py      # scrub keys + status bar + _apply_scrub + store sub

tests/
├── unit/
│   ├── test_snapshot_at.py    # reduce-first-k equality + isolation + clamp
│   └── test_timeline.py       # cursor ops, clamp, toggle, label
└── integration/
    └── test_console_app.py     # (extend) pause/step historical; resume live; paused-grows

docs/quickstart.md  README.md   # scrub keys
```

**Structure Decision**: reconstruction is a pure `Store` method; the cursor logic
is an engine-free `Timeline`; the bridge gains a minimal hold/release; the
ConsoleApp wires keys + a status bar. No new widget — existing bound widgets
render the held snapshot unchanged.

## Complexity Tracking

No constitutional violations — table intentionally empty.
