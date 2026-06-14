# Feature Specification: Live Follow & Record

**Feature Branch**: `016-follow-and-record`

**Created**: 2026-06-14

**Status**: Draft

**Input**: Road-to-1.0 item 2 — round out live watching. Two small, expected
ergonomics: **follow** a growing stream file (like `tail -f`), and **record** the
run you're watching to a file you can replay later.

## Overview

Today `intui watch <file>` replays a file to EOF and stops; watching a *live*
producer means spawning it. This adds the two missing live ergonomics:

- **Follow**: `intui watch --follow <file>` (and `NdjsonStreamSource(path,
  follow=True)`) reads the file, then keeps reading lines as they are appended —
  so you can point the console at a log another process is still writing.
- **Record**: a key in the console saves the run seen so far to a canonical
  `.jsonl` file, so a live or adapted run can be captured and replayed later with
  plain `intui watch <file>` (no adapter needed — recorded events are canonical).

Both are thin: follow is a polling tail on the existing ndjson source; record
writes the store's accepted events via the existing recording writer.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Follow a growing file (Priority: P1)

A developer points the console at a `.jsonl` file another process is still
appending to; the console renders the existing events and then keeps updating as
new lines are written, until the user quits.

**Why this priority**: Tailing a live log is the most common "watch it happen"
case that the file replayer doesn't cover.

**Independent Test**: Write some lines to a file; start `NdjsonStreamSource(path,
follow=True)` into a store; assert the initial events reduce; append more lines;
assert the new events reduce; cancel the run cleanly.

**Acceptance Scenarios**:

1. **Given** a `.jsonl` file with N events, **When** followed, **Then** those N
   reduce and the stream stays live (does not end at EOF).
2. **Given** the followed file, **When** more lines are appended, **Then** the new
   events reduce as they arrive.
3. **Given** a line written in pieces (no trailing newline yet), **When** the rest
   arrives, **Then** the completed line is parsed once (no partial/garbled event).
4. **Given** the user quits, **When** the app stops, **Then** the follow loop ends
   cleanly (no hang).

---

### User Story 2 - Record the run to a replayable file (Priority: P1)

While watching (live, followed, or adapted), the developer presses a key and the
run seen so far is saved to a canonical `.jsonl` file; later they
`intui watch <that file>` and get the same console.

**Why this priority**: Capturing a live/adapted run for later replay (sharing, a
bug repro, a fixture) is the natural companion to live watching.

**Independent Test**: Drive events into a console; trigger the record action;
assert the file contains the accepted events as canonical envelopes that reduce
into the same state on replay.

**Acceptance Scenarios**:

1. **Given** a console with events, **When** the record key is pressed, **Then** a
   `.jsonl` file is written containing the accepted events (canonical envelopes)
   and the user is told the path.
2. **Given** that file, **When** replayed with `intui watch <file>`, **Then** it
   reconstructs the same state (round-trips).
3. **Given** an adapted/wrapped source (e.g. IntentForge), **When** recorded,
   **Then** the file is **canonical** (no wrapper) and replays with no adapter.

---

### Edge Cases

- Following a file that does not exist yet: a clear error (or waits) — v1 requires
  the file to exist when the watch starts (clear error otherwise).
- The followed file stops growing: the console simply idles, staying live.
- A malformed appended line: surfaced via stream health (reuse), not a crash.
- `--follow` with the `-- <command>` form: not applicable — a clear error
  (follow is for a file; a command is already live).
- Recording with no events yet: writes an empty (valid) file; the user is told.
- The record destination is unwritable: a clear, non-crashing error/notice.

## Requirements *(mandatory)*

### Functional Requirements

**Follow**

- **FR-001**: `NdjsonStreamSource` MUST accept `follow=False` (+ a poll interval);
  with `follow=True` over a file path it reads existing lines then keeps yielding
  appended lines until the consumer stops (the stream stays live, never ending at
  EOF).
- **FR-002**: Follow MUST handle partial lines (a line appended without its
  trailing newline yet) by waiting and parsing the line once it is complete.
- **FR-003**: `watch(..., follow=…)` and `intui watch --follow <file>` MUST expose
  follow; `--follow` with a `-- <command>` MUST be a clear error.
- **FR-004**: Follow MUST reuse the existing decode/unwrap + malformed-line
  handling; it MUST be engine-free and cancel cleanly.

**Record**

- **FR-005**: The `Store` MUST expose its accepted events (read-only) so a run can
  be saved.
- **FR-006**: The `ConsoleApp` MUST provide a record action (a key) that writes
  the accepted events to a canonical `.jsonl` file (via the existing recording
  writer) and reports the path.
- **FR-007**: Recorded files MUST be **canonical** envelopes (no producer
  wrapper) so they replay with `intui watch <file>` and no adapter.
- **FR-008**: A failed write (unwritable path) MUST be reported, not crash the
  app.

**Cross-cutting**

- **FR-009**: Follow (source) + the events accessor MUST be engine-free and
  headlessly testable; the record action via Pilot.

### Key Entities

- **Follow mode**: a polling tail on `NdjsonStreamSource` (keeps the stream live).
- **`Store.events`**: the read-only accepted-event history used to record.
- **Record action**: a console key saving the run to a canonical `.jsonl`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A followed file reduces its initial events and then new appended
  events as they arrive; the stream stays live; the loop cancels cleanly
  (verified headlessly).
- **SC-002**: The record action writes the accepted events to a `.jsonl` that
  replays into the same state (round-trip verified).
- **SC-003**: An adapted/wrapped run records as **canonical** envelopes that
  replay with no adapter (verified).
- **SC-004**: `intui watch --follow <file>` follows; `--follow -- <cmd>` errors
  clearly; partial lines parse exactly once.
- **SC-005**: Follow + the events accessor are engine-free (layering guard green).

## Assumptions

- v1 follow requires the file to exist when watching starts (no "wait for the
  file to appear"); rotation/truncation handling is best-effort (append-only is
  the assumed shape).
- Record is a **snapshot of the run so far** (accepted events at the moment of the
  keypress), written via the existing recording writer — not a continuous tee;
  pressing again later captures more. Continuous tee-to-file is a possible future
  refinement.
- Recorded events are the **accepted, canonical** events (malformed/rejected
  lines are not recorded), so the file is always clean and replayable.
- The record destination defaults to a timestamped file in the working directory;
  a custom path is a future nicety.
