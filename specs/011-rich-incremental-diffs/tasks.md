# Tasks: Rich Incremental Diffs & Assembly Nesting

**Feature**: `011-rich-incremental-diffs` | **Input**: plan.md, research.md,
data-model.md, contracts/contract-api.md

Test-first throughout (Principle VII). `[P]` = parallelizable. Gate after each
phase: `uv run pytest && uv run ruff check && uv run mypy`.

## Phase 1 — Accumulate diffs by path (kit)

- [ ] **T001** [P] Extend `tests/unit/test_artifacts.py`: N `diff_ready` events
      for N paths -> diff view lists all N (first-seen order); repeat path ->
      replaced in place (no dup); `reset: true` -> clears then applies; single
      multi-file `diff_ready` still lists those files; public-safe still redacts.
- [ ] **T002** Implement accumulation in `src/intui/kit/state/artifacts.py`:
      `_reduce` diff branch merges via `_merge_files` by `raw_path` unless
      `payload.reset`; latest event supplies id/title/public_safe. Make T001 pass.

## Phase 2 — Synthesize parent nodes (kit)

- [ ] **T003** [P] Extend `tests/unit/test_kit_selectors.py`: items with
      `scope.task_id=P` and no task event nest under a synthesized node titled
      `P` (status roll-up); a later real task event for `P` takes precedence;
      items with no task_id stay under "unassigned"; mixed case coexists.
- [ ] **T004** Add `parent_id` to `WorkItemView` (`src/intui/kit/state/model.py`,
      defaulted) and set it in `_reduce_item` (`src/intui/kit/state/reduce.py`).
- [ ] **T005** Update `tree_view` (`src/intui/kit/state/selectors.py`) to group
      by actual `parent_key`, synthesize parent nodes from `parent_id` with a
      status roll-up, keep "unassigned" for parentless items. Make T003 pass.

## Phase 3 — Adapter passes suite_id

- [ ] **T006** [P] Extend `tests/unit/test_adapter_intentforge.py`:
      `assembly_item_*` and `file_diff` with `suite_id` -> `scope.task_id`=suite,
      `scope.work_item_id`=work_item_id; without `suite_id` -> task_id unset
      (backward compatible).
- [ ] **T007** Update `src/intui/adapters/intentforge.py` (`_item_*`,
      `_file_diff`) to set `scope.task_id` from `suite_id` when present. Make
      T006 pass.

## Phase 4 — Real IF 0.9.13 end-to-end

- [ ] **T008** Regenerate `examples/intentforge_console/run.ndjson` from a real
      IF 0.9.13 `assembly-benchmark --event-stream ndjson` run (multiple
      file_diffs + suite_id); keep it small/representative + public-safe.
- [ ] **T009** Extend `tests/integration/test_intentforge_console.py` (Pilot):
      the diff view lists all changed files; the tree nests the assembly items
      under the suite; no crash; public-safe by default.

## Phase 5 — Gate, docs, verify, merge

- [ ] **T010** Full gate: `uv run pytest && uv run ruff check && uv run mypy`;
      bump `src/intui/__init__.py` `__version__` to `0.11.0`.
- [ ] **T011** [P] Docs: note diff accumulation (+ `reset`) and parent nesting in
      `docs/event-stream-contract.md`; refresh the IF example README if needed.
- [ ] **T012** Fresh-build verify: `uv build` + clean-install; spot-check the IF
      example reduces all files + nesting.
- [ ] **T013** Merge: `git merge --no-ff` `011-rich-incremental-diffs` into
      `main`; update project memory (011 done; real-IF rendering rich).

## Dependencies

- T002 ← T001; T004→T005 ← T003; T007 ← T006.
- T008 ← T002+T005+T007 (needs the new behavior to assert against); T009 ← T008.
- T010–T013 last, in order.

## Parallelizable

`[P]`: T001, T003, T006, T011 — distinct files.
