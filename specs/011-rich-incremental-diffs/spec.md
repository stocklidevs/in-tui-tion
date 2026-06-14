# Feature Specification: Rich Incremental Diffs & Assembly Nesting

**Feature Branch**: `011-rich-incremental-diffs`

**Created**: 2026-06-14

**Status**: Draft

**Input**: Real-data findings from testing the IntentForge adapter (010) against
an actual `intentforge assembly-benchmark --event-stream ndjson` run: a real run
emits **many** single-file `file_diff` events (20 in the sample) that all
collapsed into one diff view entry, and assembly work items rendered flat under
"unassigned" because there was no parent task. IntentForge 0.9.13 now adds
`suite_id` (parent) + `work_item_id` to assembly + file_diff events; this feature
addresses the in-TUI-tion side.

## Overview

Two real limitations surfaced when the 010 adapter was pointed at a genuine IF
run. Both are **on our side** (the kit), and both make multi-step, multi-file
producers render poorly:

1. **Diffs collapse.** The artifacts reducer holds a *single* diff artifact and
   each `diff_ready` event **replaces** it. A producer that streams one
   `file_diff` per changed file (IF emits 20) shows only the last file. Event
   streams are append-only facts ("this file changed"), so the natural semantics
   is to **accumulate** diffs by path.
2. **Work items don't nest.** `tree_view` only nests a work item under a parent
   when an explicit `TaskView` exists for it. A producer that emits work items
   carrying a parent id (now IF's `suite_id`) but **no** task lifecycle event
   gets everything dumped into "unassigned" — losing the parent grouping.

This feature makes the kit accumulate file diffs by path and synthesize parent
nodes for work items whose parent has no explicit task event, then updates the
IntentForge adapter to pass IF 0.9.13's `suite_id` through as the parent. The
result: a real IF run shows **all** its changed files and nests its work items
under their blueprint/suite.

Non-goal (deferred): driving the activity strip from assembly-only streams (no
run/suite lifecycle event in that stream) — tracked separately.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - All changed files appear in the diff view (Priority: P1)

A producer streams one `file_diff`/`diff_ready` per changed file across a run.
The diff view lists **every** changed file, not just the most recent one.

**Why this priority**: This is the headline real-data fix — an IF run's whole
point is the set of files it changed; showing one is nearly useless.

**Independent Test**: Ingest several `diff_ready` events each carrying a
different single-file diff; assert the diff view lists all the files; ingest a
second `diff_ready` for an already-seen path; assert that file is updated in
place (not duplicated).

**Acceptance Scenarios**:

1. **Given** N `diff_ready` events for N distinct paths, **When** reduced,
   **Then** the diff view lists all N files (in first-seen order).
2. **Given** a later `diff_ready` for a path already present, **When** reduced,
   **Then** that path's diff is replaced (no duplicate row).
3. **Given** a `diff_ready` carrying `reset: true`, **When** reduced, **Then**
   the accumulated set is cleared and replaced by that event's files (a snapshot
   producer can opt out of accumulation).
4. **Given** public-safe is on (default), **When** the accumulated diffs render,
   **Then** every file stays redacted.

---

### User Story 2 - Work items nest under their parent without a task event (Priority: P1)

A producer emits work items that carry a parent id but never emits a task
lifecycle event for that parent. The tree view shows the work items grouped
under a synthesized parent node (titled by the parent id), not dumped into
"unassigned".

**Why this priority**: Real IF assembly streams carry the parent (`suite_id`)
on each item but emit no suite-level event; flat "unassigned" loses the
structure that makes the run readable.

**Independent Test**: Reduce work-item events whose scope has a `task_id` for
which no task event was seen; assert the tree groups them under a node titled by
that id; reduce items with no `task_id` at all and assert they still fall under
"unassigned".

**Acceptance Scenarios**:

1. **Given** work items with `scope.task_id = P` and no task event for `P`,
   **When** projected, **Then** the tree shows a parent node (titled `P`) with
   those items nested under it.
2. **Given** a real task event later arrives for `P`, **When** projected,
   **Then** the items nest under that real task (its title/status win).
3. **Given** work items with no `task_id`, **When** projected, **Then** they
   remain grouped under "unassigned" (unchanged behavior).

---

### User Story 3 - A real IntentForge run renders richly (Priority: P1)

Pointed at an actual IF 0.9.13 `assembly-benchmark --event-stream ndjson` run,
`intui watch --adapter intentforge` shows every changed file in the diff view
and nests the assembly work items under their suite.

**Why this priority**: This is the end-to-end proof the two kit fixes plus the
adapter change deliver the real-world payoff.

**Independent Test**: Drive a captured IF 0.9.13 stream through the adapter into
a store; assert the diff view lists all changed files and the tree nests the
items under the suite id.

**Acceptance Scenarios**:

1. **Given** a captured IF 0.9.13 stream with many `file_diff` events, **When**
   adapted and reduced, **Then** the diff view lists all the changed files.
2. **Given** assembly items carrying `suite_id`, **When** adapted, **Then** the
   adapter sets the canonical `scope.task_id` to the suite and `work_item_id` to
   the item, and the tree nests them under the suite.
3. **Given** the run, **When** rendered through `ConsoleApp`, **Then** it shows
   the files and nesting with no crash, public-safe by default.

---

### Edge Cases

- Two `diff_ready` events for the same path: the later one wins for that path;
  no duplicate row, other paths untouched.
- A `diff_ready` with an empty diff for a path: the file appears with an empty
  body (no crash) — consistent with IF dropping a redacted blob.
- A work item whose parent id later gets a real task event: it moves from the
  synthesized node to the real task; counts stay correct.
- Mixed stream: some work items with a parent id, some without — both the
  synthesized parent node(s) and the "unassigned" node coexist.
- A snapshot-style producer that re-sends a full multi-file `diff_ready` each
  time can set `reset: true` to avoid accumulating stale files.

## Requirements *(mandatory)*

### Functional Requirements

**Incremental diffs (kit)**

- **FR-001**: The artifacts reducer MUST accumulate `diff_ready` file diffs by
  path: a new path is appended, an already-seen path is replaced in place.
- **FR-002**: A `diff_ready` payload MAY carry `reset: true` to clear the
  accumulated set before applying that event's files (snapshot opt-out).
- **FR-003**: Accumulated diffs MUST preserve public-safety (default-on
  redaction in the diff view) for every file.
- **FR-004**: Existing single-event multi-file `diff_ready` behavior MUST be
  preserved (one event with a multi-file unified blob still lists those files).

**Work-item nesting (kit)**

- **FR-005**: `tree_view` MUST nest work items under their parent id even when no
  explicit task event exists for that parent, synthesizing a parent node titled
  by the parent id.
- **FR-006**: When a real task event for that parent exists, the work items MUST
  nest under the real task (its title/status take precedence over a synthesized
  node).
- **FR-007**: Work items with no parent id MUST still group under "unassigned"
  (unchanged).

**IntentForge adapter**

- **FR-008**: The adapter MUST map IF's `suite_id` (when present) to the
  canonical `scope.task_id` on `assembly_item_*` and `file_diff` events, and keep
  `work_item_id` as `scope.work_item_id`, so items nest under the suite.
- **FR-009**: The adapter MUST remain backward compatible with IF streams that
  lack `suite_id` (items fall back to "unassigned" as before).

**Cross-cutting**

- **FR-010**: All changes MUST stay engine-free where they already are (kit
  state + adapter; layering guard) and be headlessly testable; the console
  renders via Pilot.
- **FR-011**: A real (or realistic captured) IF 0.9.13 stream MUST be exercised
  end-to-end (test + the example fixture updated to the new shape).

### Key Entities

- **DiffArtifact (accumulating)**: now built up across `diff_ready` events,
  files keyed by path.
- **WorkItemView.parent_id**: the raw parent id carried so the tree can title a
  synthesized parent node.
- **tree_view (synthesized parents)**: groups items under real or synthesized
  parent nodes, falling back to "unassigned" only for truly parentless items.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: N `diff_ready` events for N paths produce a diff view listing all N
  files; a repeat path updates in place (verified headlessly).
- **SC-002**: Work items carrying a parent id with no task event nest under a
  synthesized parent node; parentless items stay "unassigned" (verified).
- **SC-003**: A captured IF 0.9.13 run shows all its changed files and nests its
  work items under the suite, through the adapter (verified headlessly + the
  example).
- **SC-004**: Public-safety and all existing diff/tree behavior are preserved
  (existing tests stay green; new behavior is additive).
- **SC-005**: `reset: true` clears accumulation (verified).

## Assumptions

- IntentForge 0.9.13 (commit `3f1f6114`) adds `suite_id` + `work_item_id` to
  `assembly_item_started/committed/failed` and `suite_id` to runtime `file_diff`
  (verified in the IF repo 2026-06-14); `case_id` is preserved for compatibility.
- Accumulate-by-path is the right default for `diff_ready` (event-sourcing: each
  diff is an append-only fact); snapshot producers opt out via `reset`.
- Evidence (`evidence_ready`) keeps its existing latest-wins semantics — only
  diffs change.
- Driving the activity strip from assembly-only streams (no run/suite lifecycle
  event) is out of scope here.
