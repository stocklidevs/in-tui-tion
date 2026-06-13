# Tasks: Task Visualization Kit

**Input**: Design documents from `/specs/002-task-visualization-kit/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/kit-api.md

**Tests**: Per Constitution Principle VII, tests for `intui.kit.state` (model, reduction, selectors) are REQUIRED and written first. Component behavior uses Pilot tests.

**Organization**: US1 (chip), US2 (tree), US3 (lanes) share the Phase-2 state model; the `mission_control` example grows with each story.

## Format: `[ID] [P?] [Story] Description`

## Phase 1: Setup

- [X] T001 Extend layer enforcement: add `intui.kit.state` to the guard test in `tests/unit/test_layering.py`, and ruff per-file-ignores for `src/intui/kit/{chip,tree,lanes}.py` + `src/intui/kit/__init__.py` in `pyproject.toml`
- [X] T002 Create `src/intui/kit/` + `src/intui/kit/state/` package skeletons and `examples/mission_control/` directory

## Phase 2: Foundational (shared state model — blocks all stories)

- [X] T003 [P] Failing tests for view models in `tests/unit/test_kit_model.py`: frozen/value-equality of TaskView/WorkItemView/LaneView/TaskBoardState, status presentation table completeness (glyph+label for every core status + fallback)
- [X] T004 [P] Failing tests for the standard reduction in `tests/unit/test_kit_reduce.py`: every mapping-table row, upsert/out-of-order tolerance, orphan work items → `UNASSIGNED_KEY`, duplicate ids across runs distinct, unknown event types pass through, unknown statuses preserved
- [X] T005 Implement `src/intui/kit/state/model.py` (views, TaskBoardState, status vocabulary, STATUS_PRESENTATION)
- [X] T006 Implement `src/intui/kit/state/reduce.py` (`taskboard_slice()` per data-model.md mapping)
- [X] T007 Create committed parallel-worker fixture `tests/replay/fixtures/parallel_run.jsonl` (tasks + work items + two overlapping lanes; includes a blocked task and a failed item) and determinism test in `tests/replay/test_kit_fixture.py`
- [X] T008 [P] Failing tests for selectors in `tests/unit/test_kit_selectors.py`: chip counts (incl. empty state + `other` bucket), tree shape (nesting, unassigned bucket, ordering), lanes (scope filter, terminal flag); memoization/value-equality
- [X] T009 Implement `src/intui/kit/state/selectors.py` (`chip_view`/`tree_view`/`lanes_view` factories + view dataclasses)
- [X] T010 Implement `BoundContainer` in `src/intui/widgets/bound.py` (selector binding + value-equality `sync_view`, bridge registration) with Pilot test in `tests/snapshot/test_bound_container.py`

**Checkpoint**: state model + container base complete, headlessly tested.

## Phase 3: User Story 1 — Task counter chip (P1) [MVP]

- [X] T011 [US1] Pilot tests (write first) in `tests/snapshot/test_kit_chip.py`: counts track replayed fixture, expand/collapse via keyboard and click, per-task rows with glyph+label, status-count footer, empty state, narrow fallback form
- [X] T012 [US1] Implement `TaskCounterChip` in `src/intui/kit/chip.py` (BoundContainer: header line + collapsible scrollable row list; expansion local state)
- [X] T013 [US1] Create `examples/mission_control/` skeleton (app.py, __main__.py, recording.jsonl with parallel run) showing the chip over the taskboard slice; verify `uv run python -m examples.mission_control`

**Checkpoint**: chip demonstrable against the recorded run.

## Phase 4: User Story 2 — Two-level task tree (P2)

- [X] T014 [US2] Pilot tests (write first) in `tests/snapshot/test_kit_tree.py`: top-level tasks with status + expand affordance, work items appear indented on expand, expansion preserved across stream updates, blocked task identifiable collapsed, unassigned bucket rendered, keyboard navigation moves visible cursor
- [X] T015 [US2] Implement `TaskTree` in `src/intui/kit/tree.py` (wraps engine Tree; one-way sync from TreeView preserving expansion by task key)
- [X] T016 [US2] Add the tree to `examples/mission_control/app.py`

**Checkpoint**: tree demonstrable; chip + tree coexist.

## Phase 5: User Story 3 — Parallel lanes (P2)

- [X] T017 [US3] Pilot tests (write first) in `tests/snapshot/test_kit_lanes.py`: one lane per worker (name, activity, Signal indicator, last summary), independent updates from interleaved events, terminal lane stops animating, parent-scope filtering
- [X] T018 [US3] Implement `LanesPanel` + lane row in `src/intui/kit/lanes.py` (Signal per lane; steady on terminal)
- [X] T019 [US3] Add the lanes panel to `examples/mission_control/app.py`

**Checkpoint**: all three components live in the example.

## Phase 6: Polish & Cross-Cutting

- [X] T020 [P] Kit public API: `src/intui/kit/__init__.py` + `src/intui/kit/state/__init__.py` re-exports; extend contract-drift test in `tests/unit/test_public_api.py` with the kit-api.md names
- [X] T021 [P] SC-003 scale test in `tests/snapshot/test_kit_scale.py`: 500 tasks — chip expand and tree navigation stay responsive; counts derived without rendering all rows
- [X] T022 [P] Accessibility audit additions in `tests/snapshot/test_accessibility.py`: kit interactions keyboard-only (SC-004); all statuses color-free identifiable (SC-005)
- [X] T023 [P] `examples/mission_control/README.md` (run steps, keys) + root README mention of the kit
- [X] T024 Full gate: `uv run pytest && uv run ruff check && uv run mypy`; SC-002 check (≤15 lines per component in the example); fix all findings

## Dependencies & Execution Order

```text
Setup -> Foundational (T003-T010) -> US1 (MVP) -+-> US2 -+
                                                +-> US3 -+-> Polish
```

- US2/US3 are independent of each other after US1's example skeleton (T013); only example edits (T016/T019) serialize.
- Within every phase: test tasks strictly before implementation (Principle VII).

## Implementation Strategy

MVP = Phases 1–3 (chip working in the example). Then US2 and US3 in
priority order, Polish last. Example grows per story (Principle VIII).
