# Implementation Plan: Task Visualization Kit

**Branch**: `002-task-visualization-kit` | **Date**: 2026-06-12 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/002-task-visualization-kit/spec.md`

## Summary

First component-kit slice: a shared, engine-free task/lane state model with
a ready-made reduction of the standard event vocabulary, three Textual
components consuming it (TaskCounterChip, TaskTree on the engine's `Tree`,
LanesPanel reusing Signal), a `BoundContainer` base extending the
foundation's binding contract to container widgets, and a new gallery
example (`mission_control`) replaying a parallel-worker run. Decisions in
[research.md](research.md); mapping table and view shapes in
[data-model.md](data-model.md).

## Technical Context

**Language/Version**: Python 3.11–3.13 (unchanged)

**Primary Dependencies**: Textual 6.x (already present). **No new runtime
dependencies.**

**Storage**: JSONL recordings (unchanged).

**Testing**: pytest headless for `intui.kit.state` (model, reduction,
selectors, fixtures); Pilot/snapshot for components; SC-003 scale test with
500 tasks.

**Target Platform**: unchanged (Windows/macOS/Linux/WSL terminals).

**Project Type**: library + examples gallery (unchanged).

**Performance Goals**: components re-render only on view-model change;
responsive at ≥100 events/s (FR-013); 500-task interactions within a render
frame (SC-003).

**Constraints**: `intui.kit.state` engine-free (lint + guard test);
expansion is local UI state (research R5); no per-component color literals —
theme tokens only (FR-015).

**Scale/Scope**: three components + state model + one example. Command
menu, diff viewer, evidence panels, filtering/search: later features.

## Constitution Check

| # | Principle | Status | Notes |
|---|-----------|--------|-------|
| I | Structured State | ✅ PASS | Components consume selectors over the snapshot; the ready-made reduction is an ordinary slice reducer. |
| II | Layered Architecture | ✅ PASS | Kit (layer 2) uses only the 001 public API plus the new `BoundContainer` foundation addition; `intui.kit.state` joins the engine-free core enforcement. |
| III | Actions Are Intents | ✅ PASS | Expand/collapse/navigate are local UI state (research R5); no store mutation from components. |
| IV | Keyboard-First, Accessible | ✅ PASS | Tree navigation via engine Tree (visible cursor); chip toggle keyboard-bound; glyph+label on every status (SC-004/005). |
| V | Meaningful Motion | ✅ PASS | Lane indicators reuse Signal, driven by lane status; terminal lanes stop animating. |
| VI | Public-Safe | ✅ PASS (scoped) | Kit renders summaries/titles already in the stream; no new evidence surfaces. |
| VII | Test-First, Replayable | ✅ PASS | Model/reduction/selectors developed against recorded fixtures headlessly; component behavior via Pilot. |
| VIII | Example-Driven | ✅ PASS | New `examples/mission_control` with a parallel-worker recording (FR-016, SC-002 measured there). |
| — | New deps justified | ✅ PASS | None added. |

**Post-Phase-1 re-check (2026-06-12)**: design artifacts add no dependencies
and respect the boundaries. GATE: PASS — Complexity Tracking empty.

## Project Structure

### Documentation (this feature)

```text
specs/002-task-visualization-kit/
├── plan.md  research.md  data-model.md  quickstart.md
├── contracts/kit-api.md
├── checklists/requirements.md
└── tasks.md (Phase 2 via /speckit-tasks)
```

### Source Code (repository root)

```text
src/intui/
├── kit/
│   ├── __init__.py          # public kit re-exports
│   ├── state/               # ── engine-free (lint ban + guard test) ──
│   │   ├── model.py         # TaskView/WorkItemView/LaneView/TaskBoardState,
│   │   │                    #   status vocabulary, STATUS_PRESENTATION
│   │   ├── reduce.py        # taskboard_slice(): standard vocabulary mapping
│   │   └── selectors.py     # chip_view/tree_view/lanes_view factories
│   ├── chip.py              # TaskCounterChip
│   ├── tree.py              # TaskTree (wraps engine Tree)
│   └── lanes.py             # LanesPanel (+ lane row with Signal)
└── widgets/
    └── bound.py             # + BoundContainer base (foundation addition)

tests/
├── unit/                    # kit model/reduction/selector tests (headless)
├── replay/fixtures/
│   └── parallel_run.jsonl   # parallel-worker fixture (committed)
└── snapshot/                # chip/tree/lanes Pilot tests, SC-003 scale test

examples/mission_control/    # README.md, app.py, __main__.py, recording.jsonl
```

**Structure Decision**: kit as `intui.kit` with an engine-free `state`
subpackage mirroring the 001 enforcement pattern (research R1); components
are `BoundContainer`s registered with the existing StoreBridge unchanged
(research R3).

## Complexity Tracking

No constitutional violations — table intentionally empty.
