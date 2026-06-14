# Tasks: Zero-Config Console Runner

**Feature**: `009-console-runner` | **Input**: plan.md, research.md, data-model.md,
contracts/contract-api.md

Test-first throughout (Principle VII). `[P]` = parallelizable (independent
files). Gate after each phase: `uv run pytest && uv run ruff check && uv run mypy`.

## Phase 1 — Engine-free stream sources

- [ ] **T001** [P] Write `tests/unit/test_sources_ndjson.py`: bare envelope
      passthrough; wrapped-record unwrap (`event_record_types`); non-event record
      ignored; malformed line → `{"__malformed__", "line_number"}`; blank skipped;
      accepts a path AND a sync line iterable. (Tests fail — source absent.)
- [ ] **T002** [P] Write `tests/unit/test_sources_subprocess.py`: spawn
      `sys.executable -c "<print 2 canonical ndjson lines>"`, drive through a
      `Store`, assert events reduced and stream ENDED; spawn a bogus command,
      assert `Store.run` returns DISCONNECTED (no raise).
- [ ] **T003** Implement `NdjsonStreamSource` in `src/intui/events/sources.py`
      (shared decode/unwrap helper; path | sync-iter | async-iter; rate pacing).
- [ ] **T004** Implement `SubprocessSource` in `src/intui/events/sources.py`
      (`asyncio.create_subprocess_exec`, stdout line read, reuse decode/unwrap).
- [ ] **T005** Export both from `src/intui/events/__init__.py` (+ `__all__`); make
      T001/T002 pass.

## Phase 2 — Promote the run-status slice

- [ ] **T006** [P] Write `tests/unit/test_run_status_slice.py`: each lifecycle
      type → expected activity state; unknown type passes through; initial `idle`;
      `RUN_STATUS_EVENT_TYPES ⊆ KNOWN_EVENT_TYPES`.
- [ ] **T007** Create `src/intui/kit/state/run_status.py`:
      `RUN_STATUS_EVENT_TYPES`, `run_status_reducer`, `run_status_slice()`.
- [ ] **T008** Export from `src/intui/kit/state/__init__.py` (+ `__all__`) and
      union `RUN_STATUS_EVENT_TYPES` into `KNOWN_EVENT_TYPES`; make T006 pass.
- [ ] **T009** Refactor `examples/operator_console/app.py` to import
      `run_status_slice` and delete its local `run_status_reducer` (no behavior
      change; example still runs).

## Phase 3 — Batteries-included console (Pilot)

- [ ] **T010** [P] Add a small canonical demo fixture
      `examples/operator_console/recording.jsonl` is reused; if it carries
      mode/prompt events the viewer ignores, add a lean
      `specs/009-console-runner/contracts/demo.jsonl` (tasks + diff + evidence +
      conversation + lifecycle) for the integration test.
- [ ] **T011** Write `tests/integration/test_console_app.py` (Pilot): build a
      `ConsoleApp` over the fixture via `MemorySource`/`NdjsonStreamSource`,
      `app.run_test()`, drain to stream end; assert taskboard/conversation/diff/
      evidence reduced; press `t`/`l`/`d`/`e` and assert the central view id
      switches; build with `public_safe=False` and assert diff/evidence
      unredacted; assert stream-ended health is reflected.
- [ ] **T012** Implement `src/intui/console/app.py`: `ConsoleApp(IntuiApp)`
      (compose, `handle_intent` for `select_view`/`open_palette`, activity
      selector) + `build_console(source, *, public_safe, sweep_seconds)`.
- [ ] **T013** Implement `src/intui/console/__init__.py` exporting `ConsoleApp`,
      `build_console`, `watch`; make T011 pass.

## Phase 4 — `watch()` one-liner + CLI entry point

- [ ] **T014** Implement `src/intui/console/runner.py`: `watch(source, *,
      public_safe, rate)` (path → `NdjsonStreamSource` with
      `event_record_types=("run_trace_event",)`; EventSource → direct;
      `build_console` + `.run()`).
- [ ] **T015** [P] Write `tests/unit/test_console_cli.py`: `main(["watch",
      "<missing>.jsonl"])` returns non-zero + `error:` on stderr (no traceback);
      `main(["watch", "--", "definitely-not-a-cmd"])` → non-zero + clear message;
      arg parsing picks file vs `--` command form and `--no-public-safe`/`--rate`.
      (Stub `ConsoleApp.run`/`watch` so no terminal is needed.)
- [ ] **T016** Implement `src/intui/console/cli.py`: `argparse` parser
      (`watch` subcommand, `--public-safe/--no-public-safe`, `--rate`, positional
      file vs `-- cmd…`), `main(argv) -> int`, clear-error handling for missing
      file / spawn failure; make T015 pass.
- [ ] **T017** Add `[project.scripts] intui = "intui.console.cli:main"` to
      `pyproject.toml`.

## Phase 5 — Layering, docs, gate, verify

- [ ] **T018** Extend `tests/unit/test_layering.py` (or rely on the existing
      subprocess guard) to confirm the new sources stay engine-free and that
      `intui` root import does NOT pull in `intui.console`/Textual.
- [ ] **T019** [P] Add a "zero-config runner" section to `docs/quickstart.md`
      (`intui watch run.jsonl`, `intui watch -- <cmd>`, `from intui.console
      import watch`) and `specs/009-console-runner/quickstart.md`.
- [ ] **T020** [P] Update `README.md` with the `intui watch` one-liner near the
      install instructions.
- [ ] **T021** Full gate: `uv run pytest && uv run ruff check && uv run mypy`;
      bump `src/intui/__init__.py` `__version__` to `0.9.0`.
- [ ] **T022** Fresh-build verify: `uv build`; clean-install the wheel into a
      throwaway env (`uv pip install --python <py> <wheel>`); confirm `intui
      watch <demo>.jsonl` is on PATH and launches (or `intui --help` works
      headlessly), and `from intui.console import watch` imports.
- [ ] **T023** Merge: `git merge --no-ff` `009-console-runner` into `main`;
      update project memory (feature 009 done, roadmap → feature 010 IF adapter).

## Dependencies

- T003–T004 depend on T001–T002 (tests first); T005 unblocks Phase 3/4.
- T007–T008 depend on T006; T009 depends on T008.
- T012–T013 depend on T005 + T008 (sources + slice); T011 first.
- T014/T016 depend on T013; T015 first; T017 after T016.
- T018–T020 any time after the code lands; T021–T023 last, in order.

## Parallelizable

`[P]`: T001/T002 (different test files), T006, T010, T015, T019, T020 — distinct
files, no shared edits.
