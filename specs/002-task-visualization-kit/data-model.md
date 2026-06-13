# Data Model: Task Visualization Kit

**Feature**: `002-task-visualization-kit` | **Date**: 2026-06-12

All view models are immutable (frozen dataclasses) with value equality —
the re-render contract from feature 001 depends on it.

## Status vocabulary

Core statuses: `pending | active | blocked | completed | failed`.
Unknown/custom statuses are preserved verbatim and presented with the
neutral fallback style; aggregate counts bucket them under `other`.

## TaskView

| Field | Type | Notes |
|-------|------|-------|
| `key` | str | Identity: `run_id:task_id` (duplicate task ids across runs stay distinct). |
| `task_id` | str | From event scope. |
| `title` | str | From `summary`/payload `name`; falls back to `task_id`. |
| `status` | str | Latest known status (out-of-order tolerant: last event wins by arrival). |
| `item_counts` | Mapping[str, int] | Child work-item counts by status. |
| `last_summary` | str \| None | Most recent event summary for this task. |
| `order` | int | First-seen index (stable presentation order). |

## WorkItemView

| Field | Type | Notes |
|-------|------|-------|
| `key` | str | `run_id:work_item_id`. |
| `work_item_id` | str | From event scope. |
| `parent_key` | str | Owning TaskView key, or the literal `unassigned` bucket key when the parent is unknown (US2-5). |
| `title` | str | From summary/payload; falls back to id. |
| `status` | str | Latest known status. |
| `last_summary` | str \| None | |

## LaneView

| Field | Type | Notes |
|-------|------|-------|
| `key` | str | `run_id:lane_id`. |
| `name` | str | From payload `name`/`role`; falls back to lane id. |
| `parent_key` | str \| None | Owning task key when scoped (FR-012). |
| `activity` | str | Current activity text (last `subagent_activity` summary). |
| `status` | str | `active` while running; terminal status from the completion event. |
| `terminal` | bool | True once completed — lanes stop animating (US3-3). |
| `last_summary` | str \| None | |

## TaskBoardState

The derived slice consumed by all selectors/components.

- `tasks`: ordered mapping key → TaskView
- `work_items`: ordered mapping key → WorkItemView
- `lanes`: ordered mapping key → LaneView
- Derived aggregates (via selectors, not stored): total/completed counts,
  counts by status (with `other` bucket), items per task, lanes per scope.

## Standard event mapping (FR-002)

| Event type | Effect on TaskBoardState |
|------------|--------------------------|
| `task_created` | Upsert TaskView, status `pending`. |
| `task_started` | Upsert TaskView, status `active`. |
| `task_completed` | Upsert; status `failed` if event status is `failed`, else `completed`. |
| `task_blocked` | Upsert TaskView, status `blocked`. |
| `work_item_started` | Upsert WorkItemView, status `active`; parent from scope `task_id`, else `unassigned`. |
| `work_item_completed` | Upsert; status `failed` if event status is `failed`, else `completed`. |
| `subagent_started` | Upsert LaneView, status `active`, name from payload. |
| `subagent_activity` | Update lane `activity` + `last_summary`. |
| `subagent_completed` | Lane terminal; status from event status (default `completed`). |
| anything else | State unchanged (foundation reducer contract). |

Upsert semantics give out-of-order tolerance: any event referencing an
unseen task/item/lane creates it with what the event knows (US edge cases).

## Components (presentation contracts)

- **TaskCounterChip**: collapsed = `{completed} / {total} tasks complete`
  (narrow fallback `{completed}/{total}`; empty state `no tasks`). Expanded
  = scrollable rows `glyph label  title` + a counts-by-status footer when
  non-binary statuses exist. Expansion is local UI state (research R5).
- **TaskTree**: top level = TaskViews (status glyph + label + title);
  children = WorkItemViews indented. Expansion per task, preserved across
  refreshes by task key. Keyboard: move/expand/collapse with visible cursor
  (engine Tree behavior).
- **LanesPanel**: one row per LaneView (optionally filtered by
  `parent_key`): Signal (status-driven motion; steady when terminal) +
  name + activity + last summary.

## Status presentation (shared)

| Status | Glyph | Label | Theme token |
|--------|-------|-------|-------------|
| pending | `·` | pending | muted |
| active | `»` | active | thinking |
| blocked | `▲` | blocked | waiting |
| completed | `✔` | done | success |
| failed | `✘` | failed | failure |
| (other) | `?` | as-is | muted |

Glyph + label are the mandatory non-color counterparts (SC-005).
