# Phase 0 Research: Task Visualization Kit

**Feature**: `002-task-visualization-kit` | **Date**: 2026-06-12

The big platform decisions were made in feature 001 (Textual 6.x engine,
engine-free pipeline core, uv/pytest tooling). This phase resolves only the
kit-specific unknowns.

## R1. Kit package layout: `intui.kit` with an engine-free `state` core

**Decision**: New subpackage `src/intui/kit/`:

- `intui/kit/state/` — **engine-free**: view-model dataclasses (`model.py`),
  the ready-made event reduction (`reduce.py`), and selectors
  (`selectors.py`). Added to the layering guard and the ruff `textual` ban.
- `intui/kit/chip.py`, `tree.py`, `lanes.py` — the Textual components
  (exempted from the ban like `intui.widgets`).

**Rationale**: Mirrors the 001 split exactly: everything testable headlessly
stays engine-free (FR/SC demand headless model tests), and the layer
boundary stays mechanical (lint + guard test), not aspirational.

**Alternatives considered**: components under `intui.widgets` (blurs
layer 2 vs the foundation's rendering primitives); a separate distribution
package (overkill at this stage).

## R2. Task tree built on Textual's `Tree` widget

**Decision**: `TaskTree` wraps Textual's built-in `Tree` widget, syncing
nodes from the view model on refresh (data-driven, one-way).

**Rationale**: `Tree` already provides keyboard navigation, visible focus
(cursor), expand/collapse, scrolling, and accessibility-friendly affordances
— re-implementing those violates "prefer the engine's built-ins"
(constitution constraints). The kit's job is the data direction: view model
in, tree nodes out, expansion state preserved across refreshes.

**Alternatives considered**: custom row-rendering widget (full control, but
re-implements navigation/scrolling for no spec-driven reason).

## R3. Container components: a `BoundContainer` base alongside `BoundWidget`

**Decision**: Add `intui.widgets.BoundContainer` — same selector-binding and
value-equality refresh contract as `BoundWidget`, but a container (composes
child widgets) instead of a Static. The chip (header + collapsible list),
tree (wrapping `Tree`), and lanes panel (stack of lane rows) are
`BoundContainer`s. The `StoreBridge` already accepts anything implementing
`refresh_from(snapshot)`; no bridge changes needed.

**Rationale**: The foundation's `BoundWidget` is render-to-text; the kit's
components have interactive children (list, tree, per-lane signals). One
shared base keeps re-render-on-change semantics uniform (FR-013).

**Alternatives considered**: making every component render pure text
(loses Tree/ListView interactivity); per-component ad hoc subscriptions
(duplicated logic, easy to violate coalescing).

## R4. Standard event mapping lives in the kit, vocabulary frozen in data-model.md

**Decision**: `intui.kit.state.reduce.taskboard_reducer` implements the
mapping table in data-model.md (the requirements doc vocabulary:
`task_created/started/completed/blocked`, `work_item_started/completed`,
`subagent_started/activity/completed`). Unknown event types pass through
unchanged (foundation reducer contract). Apps mount it as a slice via
`compose_reducers(taskboard=taskboard_slice())` and may replace it entirely
(FR-003) — components only see view models.

**Rationale**: Batteries included without coupling: the mapping is data
(one table), the components are vocabulary-agnostic.

## R5. Expansion state is local UI state, not store state

**Decision**: Chip expansion and tree node expansion live in the widgets
(local UI state), preserved across view-model refreshes by task identity.
They are not events, not intents, and never touch the store.

**Rationale**: Principle III separates application state (events/intents)
from presentation state. Which nodes are unfolded is presentation; pushing
it through the store would make every keystroke a state mutation and
pollute recordings.

**Alternatives considered**: expansion-as-intent (only justified once a
host app wants to drive expansion remotely — out of scope, R13 modes can
revisit).

## R6. Scale strategy for SC-003 (500 tasks)

**Decision**: The chip's expanded list and the lanes panel cap visible rows
to the scroll viewport via their containers (Textual handles virtualization
for `Tree`; the chip list uses a scrollable container). Counts and
aggregates come from the state model, never from rendered rows. The SC-003
test loads 500 tasks and asserts interaction latency stays within one
render frame budget.

**Rationale**: Derived aggregates + viewport rendering is what keeps "no
unbounded rendering work" true regardless of task count.
