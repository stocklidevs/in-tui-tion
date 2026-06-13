# Feature Specification: Task Visualization Kit

**Feature Branch**: `002-task-visualization-kit`

**Created**: 2026-06-12

**Status**: Draft

**Input**: User description: "Task visualization component kit: task counter chip, collapsible two-level task tree, and parallel subagent lanes"

## Overview

The first slice of the component kit (constitution layer 2): three reusable,
data-driven components that make units of work visible — a compact **task
counter chip**, a **collapsible two-level task tree**, and a **parallel lanes
panel**. Together they are the heart of an operator console, but each is
framed generically: a "task" is any unit of work (plan steps, CI jobs, batch
imports), and a "lane" is any concurrent worker (subagents, runners, queues).

All three consume view models derived from the event pipeline shipped in
feature 001. The kit also provides a ready-made reduction from the common
task/lane event vocabulary, so applications emitting standard events get
these components with near-zero glue — while apps with custom state can bind
their own view models.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Glanceable progress with the task counter chip (Priority: P1)

A developer adds a compact chip to their TUI showing overall progress, e.g.
`7 / 14 tasks complete`. An end user glances at it to know how far along the
work is, and expands it (keyboard or mouse) into a task list showing each
task's status; collapsing returns to the compact chip.

**Why this priority**: The chip is the smallest complete, useful unit of the
kit — glanceable progress plus drilldown is the single most-requested
operator need, and it establishes the kit's shared task state model that the
tree and lanes build on.

**Independent Test**: Replay a recorded run that creates and completes tasks;
verify the chip's counts track the events, and that expanding/collapsing via
keyboard shows/hides the task list.

**Acceptance Scenarios**:

1. **Given** a stream where 14 tasks were created and 7 completed, **When**
   the chip renders, **Then** it shows `7 / 14 tasks complete`.
2. **Given** a collapsed chip, **When** the user activates it (keyboard key
   or click), **Then** an expanded list appears showing every task with a
   per-task status indicator (symbol + label, not color alone), and counts
   by status when statuses beyond done/not-done exist.
3. **Given** an expanded chip, **When** a task completes in the stream,
   **Then** both the counts and the task's row update without any other UI
   disturbance.
4. **Given** a stream with zero tasks, **When** the chip renders, **Then** it
   shows an explicit empty state (e.g., `no tasks`) rather than `0 / 0`.

---

### User Story 2 - Drill into work with the two-level task tree (Priority: P2)

An end user watches high-level, user-facing tasks stay visible while being
able to expand any task to reveal its lower-level work items (tool calls,
generated artifacts, verification gates — whatever the application reports).
Collapsing a task hides the detail again. Keyboard navigation moves between
tasks and into/out of detail levels.

**Why this priority**: The two-level model (R4) is what separates an operator
workbench from a flat to-do list — but it needs the task state model US1
establishes.

**Independent Test**: Replay a recorded run with tasks and nested work items;
verify expand/collapse per task, correct parent/child association, and that
status changes at either level render at the right row.

**Acceptance Scenarios**:

1. **Given** tasks with work items, **When** the tree renders, **Then**
   top-level tasks are visible with their status and an affordance showing
   they can be expanded; work items are hidden until expanded.
2. **Given** a collapsed task, **When** the user expands it, **Then** its
   work items appear indented beneath it with their own status indicators,
   and other tasks do not move unexpectedly (no scroll jumps).
3. **Given** an expanded task, **When** a work item changes status in the
   stream, **Then** only that row's indicator updates.
4. **Given** a task marked blocked, **When** the tree renders, **Then** the
   blocked state is visually distinct by symbol and label (not color alone)
   and the task is discoverable without expanding anything.
5. **Given** an event referencing a work item whose parent task is unknown,
   **When** the tree renders, **Then** the work item is grouped under an
   explicit "unassigned" parent rather than dropped or crashing.

---

### User Story 3 - Watch concurrent work in parallel lanes (Priority: P2)

When multiple workers run concurrently, an end user sees each as a lane:
its name/role, what it is doing right now, its status with an ambient
activity indicator, and its last reported result. Lanes appear when workers
start and reach a terminal presentation when workers finish.

**Why this priority**: Parallel work is invisible in a flat list; lanes (R5)
are the component that makes concurrency legible. Depends on the same state
model but is independent of the tree.

**Independent Test**: Replay a recorded run with two overlapping workers;
verify a lane per worker with name, activity, status indicator, and last
event; verify lanes update independently as interleaved events arrive.

**Acceptance Scenarios**:

1. **Given** two workers active at once, **When** the lanes panel renders,
   **Then** each worker has its own lane showing name/role, current
   activity, a status indicator with motion (reusing the Signal primitive),
   and its last event summary.
2. **Given** interleaved activity events from both workers, **When** they
   arrive, **Then** each lane updates independently — activity on one lane
   never overwrites another.
3. **Given** a worker completes, **When** its final event arrives, **Then**
   its lane shows a terminal status (symbol + label) and stops animating.
4. **Given** a lane scoped to a parent task, **When** the lanes panel is
   placed under that task's context, **Then** only lanes belonging to that
   scope are shown.

---

### Edge Cases

- Hundreds of tasks: the expanded list and tree remain scrollable and
  responsive; the chip's counts stay accurate without rendering every row.
- Task titles longer than the available width: truncated with an ellipsis,
  never wrapped into layout-breaking overflow.
- Unknown or custom status values: rendered with the neutral fallback
  (never blank, never crash), counted under an "other" bucket.
- Out-of-order events (completion before creation): the model tolerates
  them — the task appears with its latest known status.
- Duplicate task identifiers across different runs in one stream: tasks are
  keyed by run + task identity, not title.
- A lane that emits no activity for a long time: shows its last activity
  and remains visibly idle rather than appearing frozen mid-animation.
- Terminal too narrow for the full chip text: a compact form (e.g., `7/14`)
  is used rather than clipping mid-word.

## Requirements *(mandatory)*

### Functional Requirements

**Shared task/lane state model**

- **FR-001**: The kit MUST define view-model shapes for tasks, work items,
  and lanes (identity, title, status, parent/scope linkage, last-event
  summary, timestamps) that all three components consume.
- **FR-002**: The kit MUST provide a ready-made reduction from the common
  event vocabulary (task created/started/completed/blocked, work item
  started/completed, worker started/activity/completed) into that state —
  usable with the pipeline from feature 001 without custom reducers.
- **FR-003**: Applications MUST be able to bypass the ready-made reduction
  and bind the components to their own view models of the declared shapes.
- **FR-004**: The model MUST tolerate out-of-order, unknown-status, and
  orphaned events per the edge cases above — derived state degrades
  gracefully, components never crash on stream content.

**Task counter chip**

- **FR-005**: The chip MUST render total and completed counts in a compact
  form, with an explicit empty state when no tasks exist, and a narrower
  fallback form when space is constrained.
- **FR-006**: The chip MUST be expandable and collapsible by keyboard and
  mouse, revealing a scrollable task list with per-task status indicators
  and counts by status when available.

**Task tree**

- **FR-007**: The tree MUST present two levels — user-facing tasks and their
  work items — with per-task expand/collapse, indentation, and status
  indicators at both levels.
- **FR-008**: The tree MUST support keyboard navigation across rows and
  levels (move, expand, collapse) with visible focus.
- **FR-009**: Blocked and failed tasks MUST be identifiable by symbol and
  label without expanding or relying on color (Principle IV).

**Lanes**

- **FR-010**: The lanes panel MUST render one lane per active worker with
  name/role, current activity, an animated status indicator driven by lane
  state (reusing the Signal primitive), and last event summary.
- **FR-011**: Lanes MUST update independently as interleaved events arrive
  and reach a terminal, non-animated presentation when their worker ends.
- **FR-012**: The lanes panel MUST support scoping to a parent task so it
  can be embedded in drilldown contexts.

**Cross-cutting**

- **FR-013**: All three components MUST re-render only when their bound view
  model values change, and stay responsive under streams of at least 100
  events/second (matching the foundation's responsiveness bar).
- **FR-014**: All component interactions (expand, collapse, navigate) MUST
  be local UI state or routed as intents — components MUST NOT mutate
  application state (Principle III).
- **FR-015**: Every status presentation across the kit MUST carry a
  non-color counterpart, and theming MUST flow from theme tokens with no
  per-component color literals (Principles IV/V).
- **FR-016**: The feature MUST extend the examples gallery with a runnable
  example demonstrating all three components against a recorded run with
  parallel workers (Principle VIII).

### Key Entities

- **TaskView**: identity (run + task id), title, status (open vocabulary
  with standard core: pending/active/blocked/completed/failed), counts of
  child work items by status, last-event summary, ordering hint.
- **WorkItemView**: identity, parent task linkage, title, status,
  last-event summary.
- **LaneView**: identity, name/role, parent scope (optional), current
  activity text, status, last-event summary, terminal flag.
- **TaskBoardState**: the derived slice holding all of the above plus
  aggregate counts; produced by the ready-made reduction or supplied by the
  application.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In a replayed run with 14 tasks, the chip's counts match the
  event stream at every point of the replay (verified headlessly).
- **SC-002**: A developer can add the chip, tree, or lanes to an existing
  pipeline app in under 15 lines of application code each (measured in the
  example).
- **SC-003**: With 500 tasks in state, expanding/collapsing and scrolling
  remain responsive (interactions reflected within one render frame; no
  unbounded rendering work).
- **SC-004**: 100% of kit interactions are operable by keyboard alone, with
  visible focus at all times.
- **SC-005**: With color disabled, every task/work-item/lane status in the
  example remains uniquely identifiable.
- **SC-006**: All state-model behavior (reduction, ordering tolerance,
  orphan grouping, counts) is verified by headless tests with recorded
  fixtures — zero terminal-dependent tests for model logic.

## Assumptions

- The trio ships as one feature because the components share one state
  model; command menus, diff viewers, and evidence panels are later
  features.
- The standard event vocabulary follows the names already used in the
  requirements doc and the 001 fixtures (`task_started`, `task_completed`,
  `subagent_started`, ...); the exact mapping table is a plan-phase
  decision documented in the data model.
- "Worker" naming: events use the `subagent_*`/`lane_id` vocabulary from
  the requirements doc, but the components present them generically as
  lanes/workers.
- Filtering, sorting, and search within the task list/tree are out of scope
  for this feature.
- The example may extend `hello_replay` or add a new gallery entry — plan
  decision; either satisfies FR-016.
- Mouse support follows the foundation's pattern (supplements keyboard,
  never replaces it).
