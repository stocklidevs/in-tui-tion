# Quickstart: Producer SDK (emit)

Produce a console-ready event stream from your own tool — no JSON by hand.

## A few lines

```python
from intui import run_recorder

with run_recorder("run.ndjson") as rec, rec.run():
    with rec.task("build", "Build the app") as build:
        with build.work_item("compile"):
            rec.diff("src/app.py", before=old_src, after=new_src)
        with build.work_item("test"):
            ...
    rec.evidence(pass_rate="92%", tests="14 passed", certified="gold")
```

Then render it:

```sh
intui watch run.ndjson
```

## Watch it live (no file)

Emit to stdout (the default sink) and let the runner spawn you:

```python
# my_tool.py
from intui import run_recorder

rec = run_recorder()                 # -> stdout
with rec.run():
    with rec.task("deploy", "Deploy"):
        rec.agent("starting deploy…")
        rec.diff("k8s/app.yaml", before=old, after=new)
    rec.evidence(status="green")
```

```sh
intui watch -- python my_tool.py
```

## What you can emit

- **Tasks / work items**: `rec.task(...)`, `task.work_item(...)` (context
  managers auto-emit started/completed, and `failed` if the block raises), or the
  flat `rec.task_started/completed(...)`, `rec.work_item_started/completed(...)`.
- **Diffs**: `rec.diff(path, before=…, after=…)` (built with `difflib`) — many
  calls accumulate into the diff view. Or `rec.diff_unified(text)`.
- **Evidence**: `rec.evidence(pass_rate="92%", certified="gold")`.
- **Conversation**: `rec.agent(text)`, `rec.user(text)`, `rec.system(text)`,
  `rec.question(text)`, `rec.approval(text)`.
- **Lifecycle / activity**: `rec.run()`, `rec.activity("thinking")`.
- **Anything else**: `rec.emit("custom_type", task_id=…, **payload)`.

The SDK writes **bare canonical events** (the
[contract](../../docs/event-stream-contract.md)), so `intui watch` reads them
directly — no adapter. It never redacts: your producer owns the data; the console
redacts on display by default.
