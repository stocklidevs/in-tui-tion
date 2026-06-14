# Tasks: IntentForge Adapter

**Feature**: `010-intentforge-adapter` | **Input**: plan.md, research.md,
data-model.md, contracts/contract-api.md

Test-first throughout (Principle VII). `[P]` = parallelizable (independent
files). Gate after each phase: `uv run pytest && uv run ruff check && uv run mypy`.

## Phase 1 — Pure normalizer `adapt_record`

- [x] **T001** [P] Write `tests/unit/test_adapter_intentforge.py`: per-event
      mapping (case_started→task_started w/ scope.task_id; case_finished failed→
      task_completed status failed; assembly_item_started→work_item_started w/
      work_item_id from case_id; committed/failed; assembly_plan_blocked→
      task_blocked; matrix_suite_started/finished→run_started/completed;
      file_diff→diff_ready w/ unified=payload.diff; repeat_*→message_added;
      summary→evidence_ready w/ metrics); unknown name→None; deterministic
      event_id/timestamp from sequence; accepts wrapper AND bare inner; empty/
      missing diff→diff_ready empty (no raise); validator round-trip
      (validate_event against KNOWN_EVENT_TYPES → no errors). (Tests fail.)
- [x] **T002** Create `src/intui/adapters/__init__.py` and
      `src/intui/adapters/intentforge.py`: `adapt_record`, the name→canonical
      mapping, EPOCH constant, summary metric extraction; engine-free.
- [x] **T003** Export `adapt_record` (and `IntentForgeSource`, added in Phase 2)
      from `src/intui/adapters/__init__.py`; make T001 pass.

## Phase 2 — `IntentForgeSource` + shared subprocess helper

- [x] **T004** Refactor `src/intui/events/sources.py`: extract
      `_aiter_subprocess_lines(cmd) -> AsyncIterator[str]`; have `SubprocessSource`
      decode those lines (no behavior change — 009 subprocess tests stay green).
- [x] **T005** [P] Write `tests/unit/test_intentforge_source.py`: a committed/
      inline IF-shaped ndjson (wrapper lines + summary) through a `Store` reduces
      taskboard + artifacts (diff + evidence); a spawned `sys.executable -c`
      IF-shaped producer → store ENDED; malformed line surfaced via health.
- [x] **T006** Implement `IntentForgeSource` in
      `src/intui/adapters/intentforge.py` (reads raw lines via `_aiter_text_lines`;
      `.from_command` via `_aiter_subprocess_lines`; json.loads + adapt_record;
      malformed→marker; unmapped→skip); make T005 pass.

## Phase 3 — CLI `--adapter intentforge`

- [x] **T007** [P] Extend `tests/unit/test_console_cli.py`: `--adapter
      intentforge <file>` wraps the source in `IntentForgeSource` (assert via the
      stubbed build_console source type); `--adapter intentforge -- <cmd>` uses
      `IntentForgeSource.from_command`; default `none` unchanged.
- [x] **T008** Add `--adapter {none,intentforge}` to `src/intui/console/cli.py`;
      wrap the file/subprocess source when `intentforge`; make T007 pass.

## Phase 4 — Example + fixture (Pilot)

- [x] **T009** [P] Add `examples/intentforge_console/run.ndjson`: a small but
      representative IF-shaped stream (matrix_suite_started, a case with two
      assembly items, a file_diff with a real unified diff, case_finished,
      matrix_suite_finished, trailing summary).
- [x] **T010** Implement `examples/intentforge_console/{__init__,__main__,app}.py`
      + `README.md`: build a `ConsoleApp` over `IntentForgeSource(run.ndjson)`.
- [x] **T011** Write `tests/integration/test_intentforge_console.py` (Pilot):
      the fixture renders through `ConsoleApp` — taskboard, work items, diff, and
      evidence reduced; press `d`/`e` and assert the views; stream-ended health.

## Phase 5 — Layering, docs, gate, verify, merge

- [x] **T012** Confirm the layering guard covers `intui.adapters` (add to
      CORE_PACKAGES in `tests/unit/test_layering.py` if not auto-walked) — adapter
      stays engine-free.
- [x] **T013** [P] Docs: add an "IntentForge adapter" section to
      `docs/quickstart.md` and link `specs/010-intentforge-adapter/quickstart.md`;
      README one-liner (`intui watch --adapter intentforge run.ndjson`).
- [x] **T014** Update `docs/event-stream-contract.md` with a short "Adapters"
      note (canonical is the target; IF adapter normalizes a non-canonical
      producer) if appropriate.
- [x] **T015** Full gate: `uv run pytest && uv run ruff check && uv run mypy`;
      bump `src/intui/__init__.py` `__version__` to `0.10.0`.
- [x] **T016** Fresh-build verify: `uv build`; clean-install the wheel; confirm
      `from intui.adapters import adapt_record, IntentForgeSource` imports and
      `intui watch --adapter intentforge <fixture>` parses (or `--help`).
- [x] **T017** Merge: `git merge --no-ff` `010-intentforge-adapter` into `main`;
      update project memory (010 done; IF integration loop closed).

## Dependencies

- T002–T003 depend on T001 (tests first).
- T006 depends on T004 (shared helper) + T003 (adapt_record exported); T005 first.
- T008 depends on T006; T007 first.
- T010–T011 depend on T006 + T009.
- T012–T014 after code lands; T015–T017 last, in order.

## Parallelizable

`[P]`: T001, T005, T007, T009, T013 — distinct files, no shared edits.
