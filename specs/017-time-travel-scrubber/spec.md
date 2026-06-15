# Feature Specification: Time-Travel Scrubber

**Feature Branch**: `017-time-travel-scrubber`

**Created**: 2026-06-14

**Status**: Draft

**Input**: Road-to-1.0 item 3 — the differentiator. Because everything is
immutable snapshots reduced from an append-only event log, any past state is
reconstructable. Let the user **pause, step, and rewind** a run inside the
console — a "debugger for runs" almost no bespoke dashboard has.

## Overview

The console always shows the *latest* reduced snapshot. This feature adds a
**scrubber**: pause following the live stream, step backward/forward one event at
a time, jump to the start, and resume to live. While paused, every bound widget
shows the historical state at the cursor — the run *as it was* after the first
N events — because the snapshot at N is just `reduce(events[:N])` over the pure
reducer.

Three pieces:

- **`Store.snapshot_at(n)`** — reconstruct the snapshot after the first `n`
  accepted events (pure; mirrors live per-event isolation; does not touch the
  live state).
- **`Timeline`** — a tiny engine-free cursor controller (live vs paused; step /
  start / end; position + label), pure and unit-tested.
- **Console scrubber** — keys to pause/step/rewind/resume, a status bar showing
  `n / total`, and bridge support to render a held (historical) snapshot while
  paused. Works for a finished replay *and* a still-growing live stream (the
  total keeps climbing while you inspect a frozen point).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Pause and step through a run (Priority: P1)

While watching, the user pauses; the view freezes. Stepping back shows the state
one event earlier; stepping forward advances one event. Every panel (tasks,
diff, files, metrics, …) reflects the historical state at the cursor.

**Why this priority**: Stepping through reduced state is the whole feature and
the differentiator our architecture makes cheap.

**Independent Test**: Build a store, ingest a known sequence; assert
`snapshot_at(k)` equals reducing the first `k` events; drive a `Timeline` through
pause/step and assert the cursor/position; via Pilot, pause + step and assert the
rendered widget reflects the earlier state.

**Acceptance Scenarios**:

1. **Given** N accepted events, **When** `snapshot_at(k)` is called, **Then** it
   equals the snapshot after reducing exactly the first `k` events (0 ≤ k ≤ N).
2. **Given** the console, **When** the user pauses and steps back, **Then** the
   panels show the state at `cursor-1` and the status shows the new position.
3. **Given** stepping forward at the end, **When** pressed, **Then** the cursor
   does not exceed the total (clamped).
4. **Given** an event whose reduction failed live (isolated), **When**
   reconstructing, **Then** it is skipped the same way (state matches live).

---

### User Story 2 - Rewind to start and resume to live (Priority: P1)

The user jumps to the beginning to watch from the top, then resumes to live and
the console follows the latest events again.

**Why this priority**: Start/end jumps + resume make the scrubber usable, not
just a single-step toy.

**Independent Test**: Drive the `Timeline` to start (cursor 0) and to end (live);
via Pilot, jump to start (panels empty/initial), resume to live (panels show the
latest), and confirm live following continues.

**Acceptance Scenarios**:

1. **Given** a paused run, **When** the user jumps to start, **Then** the panels
   show the initial state (cursor 0).
2. **Given** a paused run, **When** the user resumes to live, **Then** the panels
   show the latest snapshot and follow new events again.
3. **Given** the user toggles pause, **When** toggled, **Then** it freezes at the
   current latest and unfreezes back to live.

---

### User Story 3 - Scrub a still-growing live stream (Priority: P2)

While paused at event 12 of a live run, new events keep arriving; the frozen view
stays at 12 while the status total climbs; resuming jumps to the latest.

**Why this priority**: Inspecting a moment without missing the run continuing is
the realistic live-debugging case.

**Independent Test**: With a live source still publishing, pause; assert the held
snapshot stays fixed while `total` grows; resume and assert the latest renders.

**Acceptance Scenarios**:

1. **Given** a paused live run, **When** more events arrive, **Then** the rendered
   (held) snapshot does not change but the status total increases.
2. **Given** still paused, **When** the user resumes, **Then** the latest snapshot
   renders and live following continues.

---

### Edge Cases

- Scrubbing with zero events: cursor 0 = initial state; no crash.
- Stepping below 0 or above total: clamped.
- Resuming when already live: no-op.
- Reconstruction over a large history: correct (performance note — re-reduction is
  linear per step; checkpointing is a future optimization).
- Scrub keys must not hijack a focused widget's own navigation (distinct keys).
- A live stream that ends while paused: total stops growing; scrubbing still works.

## Requirements *(mandatory)*

### Functional Requirements

**Reconstruction (engine-free)**

- **FR-001**: `Store.snapshot_at(n)` MUST return the snapshot after reducing
  exactly the first `n` accepted events (clamped to `[0, len(events)]`), using the
  store's reducer, **without** mutating the live snapshot/stream.
- **FR-002**: Reconstruction MUST mirror live per-event isolation — an event whose
  reduction raises is skipped (state matches what live produced).

**Timeline controller (engine-free)**

- **FR-003**: Provide a pure `Timeline` with a cursor that is either *live*
  (follow the end) or paused at an index; with operations pause/resume(toggle),
  step(±1), to-start, to-end, a `position(total)` (clamped), and a display label.
- **FR-004**: `Timeline` MUST be immutable/deterministic (operations return new
  instances) and unit-testable headlessly.

**Console scrubber**

- **FR-005**: The `ConsoleApp` MUST provide scrub keys: pause/resume, step
  back, step forward, jump-to-start, resume-to-live; chosen to not collide with
  focused-widget navigation.
- **FR-006**: While paused, every bound widget MUST render the snapshot at the
  cursor (historical state); resuming MUST return to live rendering and follow
  new events.
- **FR-007**: A status indicator MUST show whether live or paused and the
  position (`n / total`), updating as the total grows while paused.
- **FR-008**: The bridge MUST support rendering a held (historical) snapshot
  without losing track of the latest (so resume is immediate).

**Cross-cutting**

- **FR-009**: `snapshot_at` + `Timeline` MUST be engine-free (layering guard) and
  headlessly testable; the console scrubber via Pilot.

### Key Entities

- **`Store.snapshot_at(n)`**: pure reconstruction of historical state.
- **`Timeline`**: the engine-free scrub cursor controller.
- **Bridge hold/release**: render a held snapshot while paused.
- **Scrub status bar**: live/paused + `n / total`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `snapshot_at(k)` equals reducing the first `k` events for all k,
  including isolation of failed events (verified headlessly).
- **SC-002**: `Timeline` pause/step/start/end/resume produce the correct
  positions (clamped), verified headlessly.
- **SC-003**: In the console, pause + step shows historical panel state; resume
  returns to live and keeps following (verified via Pilot).
- **SC-004**: Paused on a growing live stream, the held view stays fixed while the
  status total climbs; resume shows the latest (verified).
- **SC-005**: `snapshot_at` + `Timeline` are engine-free (layering guard green).

## Assumptions

- Reconstruction re-reduces from the initial state each call; this is linear in
  the cursor and fine for typical runs. Snapshot checkpointing for very large
  histories is a future optimization (out of scope).
- The scrubber operates over the **accepted** events the store retains
  (`Store.events`); it does not re-fetch the source.
- Scrubbing is an inspection overlay — it never mutates the run or the live
  stream; ingestion continues in the background while paused.
- Scrub keys: pause/resume, step (`,`/`.`), to-start, to-live — distinct from the
  view keys (t/l/f/d/e/m) and widget arrow navigation.
