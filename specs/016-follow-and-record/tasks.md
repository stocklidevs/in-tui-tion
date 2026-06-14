# Tasks: Live Follow & Record

**Feature**: `016-follow-and-record` | **Input**: plan.md, research.md,
data-model.md, contracts/contract-api.md

Test-first throughout (Principle VII). `[P]` = parallelizable. Gate after each
phase: `uv run pytest && uv run ruff check && uv run mypy`.

## Phase 1 — Follow (tail) on NdjsonStreamSource

- [ ] **T001** [P] Extend `tests/unit/test_sources_ndjson.py`: write a file with
      2 events, drive `NdjsonStreamSource(path, follow=True, poll_interval=0.02)`
      in a background task into a store; assert the 2 reduce and the stream stays
      LIVE; append 2 more lines; assert they reduce; append a line in two writes
      (no newline then the rest) and assert it parses once; cancel the task
      cleanly (no hang). Use a bounded wait helper.
- [ ] **T002** Add `follow`/`poll_interval` to `NdjsonStreamSource` and an
      `_aiter_followed_lines(path, poll)` helper (buffered readline + sleep) in
      `src/intui/events/sources.py`; route `__aiter__` to it when `follow` + path.
      Make T001 pass.

## Phase 2 — Store.events accessor

- [ ] **T003** [P] Add a test (`tests/unit/test_store.py` or extend an existing
      store test): `Store.events` returns accepted events in order; rejected/
      malformed are excluded; read-only (a tuple).
- [ ] **T004** Add `events` property to `src/intui/state/store.py`
      (`-> self._stream.events`). Make T003 pass.

## Phase 3 — watch() + CLI --follow

- [ ] **T005** [P] Extend `tests/unit/test_console_cli.py`: `--follow <file>`
      builds an `NdjsonStreamSource` with `follow=True`; `--follow -- <cmd>` is a
      non-zero clear error mentioning follow.
- [ ] **T006** Add `follow=False` to `watch()` (`src/intui/console/runner.py`,
      path → `NdjsonStreamSource(..., follow=follow)`); add `--follow` to
      `src/intui/console/cli.py` (file form sets follow; command form errors).
      Make T005 pass.

## Phase 4 — ConsoleApp record action

- [ ] **T007** [P] Extend `tests/integration/test_console_app.py` (Pilot): drive
      events into a console, call `action_record()` (point it at a tmp path),
      assert the file is written and `read_recording` round-trips to the same
      events; an adapted/wrapped MemorySource still records canonical events;
      a record with an unwritable path notifies and does not crash.
- [ ] **T008** Add the record action + `ctrl+s` binding to
      `src/intui/console/app.py` (write `store.events` via `write_recording` to a
      timestamped file; notify the path; catch write errors). Allow the test to
      inject the destination (e.g. a `_record_path()` seam). Make T007 pass.

## Phase 5 — Docs, gate, verify, merge

- [ ] **T009** [P] Docs: `--follow` + the record key in `docs/quickstart.md` and
      `README.md`; link the feature quickstart.
- [ ] **T010** Confirm layering: follow source + `Store.events` stay engine-free
      (`test_layering.py`).
- [ ] **T011** Full gate: `uv run pytest && uv run ruff check && uv run mypy`;
      bump `src/intui/__init__.py` `__version__` to `0.16.0`.
- [ ] **T012** Fresh-build verify: `uv build` + clean-install; spot-check
      `NdjsonStreamSource(path, follow=True)` tails an appended file and
      `write_recording(store.events)` round-trips.
- [ ] **T013** Merge: `git merge --no-ff` `016-follow-and-record` into `main`;
      update project memory (016 done; follow + record shipped; road-to-1.0 → #3
      scrubber).

## Dependencies

- T002 ← T001; T004 ← T003. T006 ← T002. T008 ← T004.
- T009–T013 last, in order.

## Parallelizable

`[P]`: T001, T003, T005, T007, T009 — distinct files.
