# Data Model: IntentForge Adapter

**Feature**: `010-intentforge-adapter` | **Date**: 2026-06-14

No new event envelope or snapshot shapes — the adapter *produces* existing
canonical envelopes (008) consumed by existing reducers (002/004/005/009). This
documents the IF input shape, the mapping, and the two new runtime objects.

## Input: IntentForge run-trace records (read-only reference)

A line is one of:

```jsonc
{"type":"run_trace_event","event":{"sequence":N,"name":"<slug>","payload":{…}}}
{"type":"summary","summary":{…}}
```

`adapt_record` accepts the wrapper, the bare inner `{sequence,name,payload}`, or
the summary record. Payload keys are IF's public-safe set (additions, case_id,
change_type, deletions, diff, duration_ms, execution_boundary, file, index,
repeat_count, run_index, status, suite_id, total, transaction_id, truncated,
work_item_id).

## Mapping: `adapt_record(record, *, run_id="intentforge") -> Event | None`

Common envelope fields for every mapped event:
`version="1"`, `event_id=f"if-{sequence}"` (`"if-summary"` for summary),
`run_id=run_id`, `timestamp=EPOCH + timedelta(seconds=sequence)` (deterministic).

| IF `name` | canonical `type` | scope | payload (canonical) | status |
|---|---|---|---|---|
| `matrix_suite_started` | `run_started` | — | — | — |
| `matrix_suite_finished` | `run_completed` | — | — | `status` |
| `case_started` | `task_started` | `task_id=case_id` | — | — |
| `case_finished` | `task_completed` | `task_id=case_id` | — | `status` (`"failed"`→failed else completed) |
| `assembly_item_started` | `work_item_started` | `work_item_id=(work_item_id or case_id)` | — | — |
| `assembly_item_committed` | `work_item_completed` | `work_item_id=…` | — | committed→completed |
| `assembly_item_failed` | `work_item_completed` | `work_item_id=…` | — | `status` (failed) |
| `assembly_plan_blocked` | `task_blocked` | `task_id=case_id` | — | `status` |
| `file_diff` | `diff_ready` | `work_item_id=(work_item_id or case_id)` | `{unified: payload.diff or "", title: payload.file or "diff", public_safe: True}` | — |
| `repeat_started` | `message_added` | — | `{role:"system", text:f"repeat {repeat_count} started (run {run_index})"}` | — |
| `repeat_finished` | `message_added` | — | `{role:"system", text:f"repeat {repeat_count} finished: {status}"}` | — |
| `summary` | `evidence_ready` | — | `{title:"IntentForge summary", metrics:[…], public_safe:True}` | — |
| (any other name) | — | — | — | returns `None` |

Notes:
- The kit's artifacts reducer parses `payload.unified` via `parse_unified_diff`,
  so the adapter just forwards IF's `diff` string as `unified` (empty string when
  IF dropped/omitted the blob — yields an empty diff, no crash; FR-004).
- `case_finished`/`assembly_item_*`/`matrix_suite_finished` set the envelope
  `status` field; the reducers read it (`"failed"`→failed).

### Summary → evidence metrics (recognized top-level keys)

Each recognized key in the summary payload becomes a metric
`{key, label, value}` (string/number value). Recognized set (present-only):
`case_pass_rate`, `quality_issue_count`, `delivered_files`,
`evidence_signature`, plus `certified_level` read from a nested `acb_score` when
present. Unknown/missing keys are skipped (FR-004). `public_safe=True` (values
are IF-public-safe).

## New runtime objects

### `adapt_record` (pure, engine-free)

```text
adapt_record(record: Mapping[str, Any], *, run_id: str = "intentforge") -> Event | None
```

Stateless per record. Unwraps a `run_trace_event` wrapper, reads
`sequence`/`name`/`payload` (or `summary`), and returns a canonical `Event` or
`None`. Never raises on missing keys (FR-004).

### `IntentForgeSource` (engine-free `EventSource`)

```text
IntentForgeSource(
    source: Path | str | Iterable[str] | AsyncIterable[str],
    *,
    run_id: str = "intentforge",
)
IntentForgeSource.from_command(cmd: Sequence[str], *, run_id: str = "intentforge")
```

Reads raw IF ndjson lines (file/iterable, or a spawned command via the shared
`_aiter_subprocess_lines` helper), `json.loads` each line, and yields
`adapt_record(...).to_mapping()` for mapped records. Malformed lines yield the
009 `{"__malformed__", "line_number"}` marker; unmapped records are skipped.

## CLI surface (extends 009)

```text
intui watch [--adapter {none,intentforge}] [--public-safe|--no-public-safe] [--rate R]
            (<file> | -- <command>)
```

`--adapter intentforge` wraps the file/subprocess input in `IntentForgeSource`.
Default `none` preserves the canonical-stream behavior from 009.

## What does NOT change

- Envelope, `Store`, stream health, snapshots, selectors, every widget, the
  `ConsoleApp`, and the canonical contract are all unchanged. IntentForge is not
  imported. The only edit to 009 code is extracting a shared subprocess
  line-reading helper (no behavior change).
