# Tasks: Producer SDK (emit)

**Feature**: `012-producer-sdk` | **Input**: plan.md, research.md, data-model.md,
contracts/contract-api.md

Test-first throughout (Principle VII). `[P]` = parallelizable. Gate after each
phase: `uv run pytest && uv run ruff check && uv run mypy`.

## Phase 1 — Recorder core + sinks + vocabulary

- [ ] **T001** [P] Write `tests/unit/test_emit.py`: list/callable sink captures
      envelopes; every helper (task_*, work_item_*, subagent_*, message/agent/
      user/system, question/approval, view/mode, activity, run_*) emits the right
      `type`/scope/payload; ids are unique+ordered (`e1`,`e2`…); injectable clock;
      generic `emit("custom", …)` works; ALL emitted events validate against
      `KNOWN_EVENT_TYPES` (no envelope errors); file sink writes ndjson + a `Path`
      round-trips via `read_recording`; reduce-through-a-store shows tasks/items.
- [ ] **T002** Implement `src/intui/emit.py`: `RunRecorder` (run_id, sink, id
      counter, clock), sink resolution (path/file/callable/stdout, flush), `emit`
      + all vocabulary helpers; `run_recorder()` factory; recorder `__enter__/
      __exit__` closes a file sink. Make T001 pass.
- [ ] **T003** Re-export `run_recorder`, `RunRecorder` from `src/intui/__init__.py`
      (+ `__all__`); confirm root import stays engine-free.

## Phase 2 — diff/evidence helpers

- [ ] **T004** [P] Extend `tests/unit/test_emit.py` (or a sibling): `diff(path,
      before, after)` emits `diff_ready` whose unified text `parse_unified_diff`
      turns into the expected file(s); identical before/after = no-change (no
      crash); `diff_unified(text)` passes text through; `evidence(**metrics)`
      emits `evidence_ready` with `{key,label,value}` rows; `public_safe` flows.
- [ ] **T005** Implement `diff`, `diff_unified`, `evidence` in `emit.py`
      (difflib unified_diff with `a/`,`b/` headers). Make T004 pass.

## Phase 3 — Context-manager lifecycle

- [ ] **T006** [P] Write `tests/unit/test_emit_lifecycle.py`: `with rec.run()`
      emits run_started then run_completed; raising → run_failed + re-raise;
      `with rec.task(id,title)` emits started then completed; raising → completed
      status=failed + re-raise; `with task.work_item(id)` emits the pair scoped to
      the task (reduce-through: item nests under the task).
- [ ] **T007** Implement `run()`, `task()` context managers + `Task`/`WorkItem`
      handles (scoped work_item; failed-on-exception) in `emit.py`. Make T006 pass.

## Phase 4 — Live path + example

- [ ] **T008** [P] Write `tests/unit/test_emit_live.py`: spawn `sys.executable -c`
      an SDK producer that emits to stdout; drive it through `SubprocessSource`
      into a store; assert events reduced + stream ENDED (no adapter, bare
      envelopes).
- [ ] **T009** Add `examples/emit_demo/{__init__,__main__,run}.py` + `README.md`:
      a small SDK producer (tasks + work items + a couple diffs + evidence) that
      emits to stdout, watchable via `intui watch -- python -m examples.emit_demo`
      and capturable to a file.

## Phase 5 — Docs, gate, verify, merge

- [ ] **T010** [P] Docs: add an "emit / produce a stream" path to
      `docs/quickstart.md`; README `run_recorder` one-liner; link the feature
      quickstart.
- [ ] **T011** Confirm `tests/unit/test_layering.py` covers `intui.emit` staying
      engine-free (it's under the `intui` walk + root-import test).
- [ ] **T012** Full gate: `uv run pytest && uv run ruff check && uv run mypy`;
      bump `src/intui/__init__.py` `__version__` to `0.12.0`.
- [ ] **T013** Fresh-build verify: `uv build` + clean-install; in a temp env emit
      a run with the SDK to a file and reduce it (and `from intui import
      run_recorder` imports).
- [ ] **T014** Merge: `git merge --no-ff` `012-producer-sdk` into `main`; update
      project memory (012 done; produce side now toothbrush-easy).

## Dependencies

- T002 ← T001; T003 ← T002. T005 ← T004 (+ T002). T007 ← T006 (+ T002).
- T008 ← T002+T003 (live needs the factory + stdout sink). T009 ← T005+T007.
- T010–T014 last, in order.

## Parallelizable

`[P]`: T001, T004, T006, T008, T010 — distinct files.
