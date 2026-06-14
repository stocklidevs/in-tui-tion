# intentforge_console

Render a real **IntentForge** run as a console — with no IF-specific code in the
console or the kit. This is feature 010 (the IntentForge adapter) on top of
feature 009 (the zero-config runner).

## Run it

```sh
uv run python -m examples.intentforge_console
```

or via the CLI, pointing the runner at the captured IF stream:

```sh
intui watch --adapter intentforge examples/intentforge_console/run.ndjson
```

## What's happening

`run.ndjson` is a captured **IntentForge** `--event-stream ndjson` stream —
lines of `{"type":"run_trace_event","event":{sequence,name,payload}}` and a
trailing `{"type":"summary",…}`. The inner records are *not* canonical
in-TUI-tion envelopes.

`IntentForgeSource` adapts each record into the canonical vocabulary
([`intui.adapters`](../../src/intui/adapters/intentforge.py)) so the standard
`ConsoleApp` renders it:

| IF event | shows up as |
|---|---|
| `case_started` / `case_finished` | a task (press `t`) |
| `assembly_item_*` | work items under the task / lanes (press `l`) |
| `file_diff` | the diff view (press `d`) |
| `matrix_suite_started/finished` | the activity strip |
| `summary` (final line) | the evidence view (press `e`) |

The adapter forwards IntentForge's already-redacted diffs; the console keeps
public-safe redaction on by default. IntentForge is **not** a dependency — the
adapter only understands its on-the-wire JSON shape.
