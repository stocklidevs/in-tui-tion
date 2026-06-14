# API Contract: Rich Incremental Diffs & Assembly Nesting

**Feature**: `011-rich-incremental-diffs` | **Date**: 2026-06-14

Behavioral guarantees tests pin. All changes are additive/semantic; no new
public symbols except a defaulted dataclass field.

## `diff_ready` (semantic change)

- Multiple `diff_ready` events accumulate: the diff view lists every distinct
  changed path (first-seen order).
- A `diff_ready` for an already-seen `raw_path` replaces that file in place (no
  duplicate).
- A `diff_ready` with payload `reset: true` clears the accumulated set first.
- A single `diff_ready` carrying a multi-file unified blob still lists all those
  files (unchanged).
- Accumulated files honor public-safe redaction by default (unchanged default).
- `evidence_ready` keeps latest-wins (unchanged).

## `WorkItemView.parent_id` (new defaulted field)

```python
WorkItemView(..., parent_id: str = UNASSIGNED_KEY)
```

- Defaulted, so existing constructions keep working.
- Set by the taskboard reducer to the raw parent id (`scope.task_id`) or
  `UNASSIGNED_KEY`.

## `tree_view` (semantic change)

- Work items whose parent id has **no** task event nest under a synthesized
  parent node titled by that id (status rolled up from the items).
- When a real task event for that parent exists, items nest under the real task
  (title/status precedence) — unchanged for task-emitting producers.
- Work items with no parent id remain under "unassigned" (unchanged).

## IntentForge adapter (semantic change)

- `assembly_item_*` and `file_diff` set `scope.task_id` from `payload.suite_id`
  when present; `scope.work_item_id` from `work_item_id` (else `case_id`).
- Streams without `suite_id` behave as before (items unassigned).
- Output still validates against `KNOWN_EVENT_TYPES` with no envelope errors.

## Backward compatibility

- No new event types; `diff_ready` gains an optional `reset` payload key.
- `WorkItemView` field is defaulted.
- Producers that emit one multi-file diff and/or real task events see identical
  behavior. Existing tests stay green; new behavior is additive.
