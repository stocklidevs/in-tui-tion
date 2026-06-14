# Quickstart: Zero-Config Console Runner

Render a full console from a canonical event stream with **zero code**.

## From the command line

Replay a captured stream file:

```bash
intui watch run.jsonl
```

Watch a live producer (it must print canonical ndjson to stdout):

```bash
intui watch -- my-agent --event-stream ndjson --task "ship it"
```

Options:

```bash
intui watch --no-public-safe run.jsonl     # show full diff/evidence (trusted local)
intui watch --rate 8 run.jsonl             # replay at 8 events/second
```

A missing file or a command that can't start prints a clear `error: …` and
exits non-zero — never a traceback.

## From Python

One line:

```python
from intui.console import watch

watch("run.jsonl")                  # a file path
watch(my_source)                    # any EventSource
watch("run.jsonl", public_safe=False, rate=8)
```

Or build the app and drive it yourself:

```python
from intui.console import build_console
from intui.events import NdjsonStreamSource

source = NdjsonStreamSource("run.jsonl", event_record_types=("run_trace_event",))
app = build_console(source, public_safe=True)
app.run()
```

## What you get

- A signature KITT **activity strip** driven by the run lifecycle.
- A persistent **conversation** panel.
- A routable **central view** — `t` tasks, `l` lanes, `d` diff, `e` evidence —
  also reachable from the command bar and palette (`ctrl+p`).
- **Public-safe by default**: diffs/evidence are redacted unless you opt out.

## What it consumes

The runner speaks the **canonical** event vocabulary (see
[`docs/event-stream-contract.md`](../../docs/event-stream-contract.md)). It
unwraps wrapped records (`{"type":"run_trace_event","event":{…}}`) and ignores
trailing non-event records (e.g. a `summary` line), so real producer output
works out of the box.

Producers whose event names differ (e.g. IntentForge's `case_started`/
`file_diff`) are normalized by a thin adapter — that's the next feature.
