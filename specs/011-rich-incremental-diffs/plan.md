# Implementation Plan: Rich Incremental Diffs & Assembly Nesting

**Branch**: `011-rich-incremental-diffs` | **Date**: 2026-06-14 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/011-rich-incremental-diffs/spec.md`

## Summary

Two kit fixes plus a one-field adapter change, all surfaced by testing the 010
adapter against a real IF run:

1. **Accumulate diffs by path** (`intui.kit.state.artifacts`): `diff_ready`
   merges its file(s) into the existing diff artifact keyed by path (new path
   appended, seen path replaced) instead of replacing the whole artifact. A
   `reset: true` payload opts out (snapshot producers). Evidence is untouched.
2. **Synthesize parent nodes** (`intui.kit.state.selectors.tree_view` +
   `WorkItemView.parent_id`): work items whose parent has no explicit task event
   nest under a synthesized node titled by the parent id (status rolled up from
   the items), instead of falling into "unassigned". Truly parentless items
   still go to "unassigned".
3. **Adapter passes `suite_id`** (`intui.adapters.intentforge`): map IF 0.9.13's
   `suite_id` to `scope.task_id` on `assembly_item_*` and `file_diff`, keeping
   `work_item_id` as `scope.work_item_id`, so items nest under their suite.

Plus refresh the `examples/intentforge_console/run.ndjson` fixture to the IF
0.9.13 shape and assert the end-to-end result. Decisions in
[research.md](research.md); shapes in [data-model.md](data-model.md).

## Technical Context

**Language/Version**: Python 3.11–3.13 (unchanged).

**Primary Dependencies**: Textual 6.x (runtime, unchanged). **No new deps.**

**Storage**: ndjson (unchanged).

**Testing**: pytest headless for the artifacts reducer (accumulate, replace-by-
path, reset, public-safe) and `tree_view` (synthesized parent, real-task
precedence, unassigned fallback) and the adapter (`suite_id` → `scope.task_id`);
an end-to-end test over a captured IF 0.9.13 stream; Pilot for the console
example.

**Target Platform**: unchanged.

**Project Type**: library + examples gallery (unchanged).

**Performance Goals**: accumulation is O(files) per event; tree projection stays
O(items + tasks).

**Constraints**: changes stay engine-free (kit state + adapter; layering guard);
public-safety preserved; existing behavior additive (no regressions); replays
deterministic.

**Scale/Scope**: artifacts reducer + tree_view + WorkItemView field + adapter
one-field map + fixture refresh. Out of scope: activity strip on assembly-only
streams; any new event types; DiffViewer widget redesign (it already lists
multiple files from `DiffView.files`).

## Constitution Check

| # | Principle | Status | Notes |
|---|-----------|--------|-------|
| I | Structured State | ✅ PASS | Diffs/items still derive from events; accumulation is reducer state. |
| II | Layered Architecture | ✅ PASS | All edits in engine-free kit state + adapter; no Textual. |
| III | Actions Are Intents | ✅ PASS (n/a) | No new actions. |
| IV | Keyboard-First | ✅ PASS (n/a) | No UI change; DiffViewer already lists files. |
| V | Meaningful Motion | ✅ PASS (n/a) | — |
| VI | Public-Safe | ✅ PASS | Accumulated diffs still redact by default (FR-003). |
| VII | Test-First, Replayable | ✅ PASS | Reducer/selector/adapter headless test-first; deterministic. |
| VIII | Example-Driven | ✅ PASS | IF example fixture refreshed to 0.9.13; e2e asserted. |
| — | New deps justified | ✅ PASS | None. |

**Post-Phase-1 re-check (2026-06-14)**: no new deps; layering holds. GATE: PASS —
Complexity Tracking empty.

## Project Structure

```text
src/intui/kit/state/
├── artifacts.py     # diff_ready accumulates by path (+ reset opt-out)
├── model.py         # WorkItemView gains parent_id
├── reduce.py        # _reduce_item sets parent_id
└── selectors.py     # tree_view synthesizes parent nodes from parent_id

src/intui/adapters/
└── intentforge.py   # assembly_item_*/file_diff: scope.task_id = suite_id

examples/intentforge_console/run.ndjson   # refreshed to IF 0.9.13 (suite_id)

tests/
├── unit/
│   ├── test_artifacts.py            # (extend) accumulate, replace-by-path, reset
│   ├── test_kit_selectors.py        # (extend) synthesized parent, precedence, unassigned
│   └── test_adapter_intentforge.py  # (extend) suite_id -> scope.task_id
└── integration/
    └── test_intentforge_console.py  # (extend) all files listed + nesting
```

**Structure Decision**: both fixes live in engine-free `intui.kit.state`
(reducer + selector + model field); the adapter change is a one-field map enabled
by IF 0.9.13. The DiffViewer widget already renders `DiffView.files`, so no
rendering-layer change is needed.

## Complexity Tracking

No constitutional violations — table intentionally empty.
