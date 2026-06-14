# Data Model: Rich Incremental Diffs & Assembly Nesting

**Feature**: `011-rich-incremental-diffs` | **Date**: 2026-06-14

No new event types or snapshot slices. Changes to existing kit shapes + reducer
semantics, and a one-field adapter map.

## `diff_ready` reduction (changed semantics)

`intui.kit.state.artifacts._reduce` for `diff_ready`:

| Condition | Result |
|---|---|
| no existing diff, or payload `reset: true` | the diff artifact = this event's parsed files (replace) |
| existing diff present | merge this event's files into the existing artifact by `raw_path` (new path appended in first-seen order; seen path replaced in place) |

The merged artifact's `id`, `title`, `public_safe` come from the latest event.
Payload gains an **optional** `reset: bool` (default false). No new event type.
`evidence_ready` is unchanged (latest-wins).

```text
_merge_files(old: tuple[FileDiff, ...], new: tuple[FileDiff, ...]) -> tuple[FileDiff, ...]
  # keyed by raw_path; preserves existing order, appends new paths
```

## `WorkItemView` (new field)

```text
WorkItemView(..., parent_id: str = UNASSIGNED_KEY)
```

`_reduce_item` sets `parent_id = event.scope.task_id` when present, else
`UNASSIGNED_KEY`. `parent_key` (the composite `run_id:task_id`) is unchanged;
`parent_id` is the raw id used to title a synthesized parent node.

## `tree_view` (synthesized parents)

```text
tree_view() -> TreeView(tasks=(TaskRow, ...))
```

Projection:
1. Group work items by `parent_key`.
2. For each real `TaskView` (sorted by order): a `TaskRow` with its grouped items
   (unchanged).
3. For each remaining group:
   - `parent_key == UNASSIGNED_KEY` → the "unassigned" `TaskRow` (unchanged).
   - otherwise → a **synthesized** `TaskRow` titled by the group's `parent_id`,
     status = roll-up of its items (`failed → blocked → active → pending` else
     `completed`).
4. Order: real tasks, then synthesized parents (first-seen), then "unassigned".

Real task events for a parent take precedence (its title/status win) — if a
`TaskView` exists, items nest under it and no synthesized node is made.

## IntentForge adapter (one-field map)

For `assembly_item_started/committed/failed` and `file_diff`:

```text
scope.task_id      = payload.suite_id   (when present; else unset)
scope.work_item_id = payload.work_item_id or payload.case_id
```

`case_id` remains the fallback for the item id (pre-0.9.13 streams), so older
streams still work (items fall back to "unassigned" without `suite_id`).

## What does NOT change

- Event envelope, store, health, snapshots, `evidence_ready`, the DiffViewer
  widget (already renders `DiffView.files`), and the canonical event *types*.
  `diff_ready` only gains an optional `reset` payload key.
