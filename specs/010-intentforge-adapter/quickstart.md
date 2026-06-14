# Quickstart: IntentForge Adapter

Render a real IntentForge run as a console — no IF-specific code.

## From the command line

Replay a captured IF stream:

```bash
intentforge assembly-benchmark … --event-stream ndjson > run.ndjson
intui watch --adapter intentforge run.ndjson
```

Watch a live IF benchmark:

```bash
intui watch --adapter intentforge -- intentforge assembly-benchmark … --event-stream ndjson
```

You get cases as tasks, assembly items as work items, file diffs in the diff
view (`d`), the run lifecycle on the activity strip, and the final summary as
evidence (`e`) — public-safe by default.

## From Python

```python
from intui.console import watch
from intui.adapters import IntentForgeSource

watch(IntentForgeSource("run.ndjson"))                       # replay a file
watch(IntentForgeSource.from_command(["intentforge", "…"]))  # live subprocess
```

Normalize a single IF record yourself:

```python
from intui.adapters import adapt_record

event = adapt_record(
    {"type": "run_trace_event",
     "event": {"sequence": 1, "name": "case_started", "payload": {"case_id": "c1"}}},
    run_id="my-run",
)
# -> canonical Event(type="task_started", scope.task_id="c1", …) or None
```

## How it maps

| IF event | becomes | shows up as |
|---|---|---|
| `case_started` / `case_finished` | `task_started` / `task_completed` | the task list |
| `assembly_item_*` | `work_item_*` | work items under a task/lane |
| `file_diff` | `diff_ready` | the diff view |
| `matrix_suite_started/finished` | `run_started` / `run_completed` | the activity strip |
| `summary` (final line) | `evidence_ready` | the evidence view |

The adapter forwards IF's already-redacted diffs; the console keeps redaction on
by default. It only understands IF's JSON shape — IntentForge is not a
dependency.
