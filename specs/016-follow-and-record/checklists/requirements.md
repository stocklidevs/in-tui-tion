# Specification Quality Checklist: Live Follow & Record

**Feature**: `016-follow-and-record`

## Content Quality

- [x] No implementation details drive the requirements (the *what*: tail a file,
      save a run; not the polling specifics).
- [x] Focused on user value (watch a live log; capture a run for replay).
- [x] Written for consumers (anyone watching/capturing a run).
- [x] All mandatory sections completed.

## Requirement Completeness

- [x] No `[NEEDS CLARIFICATION]` markers remain.
- [x] Requirements are testable (each FR → headless or Pilot test).
- [x] Success criteria measurable (follow reduces new lines + stays live; record
      round-trips; adapted→canonical; --follow errors with a command).
- [x] Success criteria technology-agnostic outcomes.
- [x] Acceptance scenarios defined (follow growing file; record→replay).
- [x] Edge cases identified (missing file, idle, malformed append, follow+cmd,
      empty record, unwritable dest, partial line).
- [x] Scope bounded — follow = polling tail; record = snapshot via existing
      writer (not a continuous tee); rotation/wait-for-file deferred.
- [x] Dependencies/assumptions identified (builds on NdjsonStreamSource 009,
      recording writer 001, ConsoleApp 009, EventStream events accessor).

## Feature Readiness

- [x] All functional requirements have clear acceptance criteria.
- [x] User scenarios cover primary flows (follow, record→replay).
- [x] Aligned with the constitution (engine-free follow + events accessor; record
      via existing writer; canonical output; replayable; keyboard-reachable).
- [x] No implementation leakage that pre-commits an internal design.

## Notes

- Deliberately thin: follow reuses the ndjson decode path; record reuses
  write_recording over the store's accepted events. Road-to-1.0 item 2 of 4.
