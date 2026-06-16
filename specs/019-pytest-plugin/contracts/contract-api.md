# API Contract: pytest Plugin

**Feature**: `019-pytest-plugin` | **Date**: 2026-06-14

## CLI option

```text
pytest --intui[=PATH]
```
- Registered by the plugin; **inert** when absent (no output, no files, no
  behavior change, pytest exit code unchanged).
- Bare `--intui` writes to a default path; `--intui=PATH` writes there.

## Emitted stream (guarantees)

For a run with the flag, the canonical ndjson contains, in order:
- one `run_started`,
- per test: a `work_item_started` then a `work_item_completed`
  (`work_item_id` = node id, `task_id` = module file), with status
  passed/failed/skipped; failures also produce a `message_added`,
- a final `evidence_ready` (passed/failed/skipped/total/duration) and a
  `run_completed` whose status is `failed` iff there were failures (or non-zero
  exit), else `passed`.

Guarantees:
- The stream is **canonical** (bare envelopes) — `intui watch <file>` /
  `--follow` / scrub / record consume it with **no adapter**.
- Reduced, it yields modules as tasks and tests as work items (parent inference)
  with correct statuses, plus the evidence summary.
- A write failure warns (pytest-side) and disables the plugin — the test run is
  never crashed by it.

## Packaging

```toml
[project.entry-points.pytest11]
intui = "intui.pytest_plugin"
```

Guarantees: auto-discovered by pytest; **no new runtime dependency** for intui
(the module is only imported within a pytest process).

## Backward compatibility

- Purely additive: a new plugin module + one entry point. No existing intui
  symbol, event type, or behavior changes. The `intui` root import does not load
  the plugin (no `pytest` import at import time).
