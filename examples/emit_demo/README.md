# emit_demo

Produce a console-ready event stream **with the Producer SDK** — no JSON written
by hand. This is feature 012 (`intui.emit`).

## Watch it live

The script emits canonical events to stdout; the runner spawns it and renders as
events arrive:

```sh
intui watch -- python -m examples.emit_demo
```

## Or capture and replay

```sh
python -m examples.emit_demo > run.ndjson
intui watch run.ndjson
```

## What's happening

Every line in [`run.py`](run.py) is a `run_recorder` call:

```python
from intui import run_recorder

rec = run_recorder()                 # default sink = stdout
with rec.run():
    with rec.task("build", "Build the app") as build:
        with build.work_item("implement"):
            rec.diff("src/calc.py", before=old, after=new)
    rec.evidence(pass_rate="100%", certified="gold")
```

The context managers auto-emit the `*_started`/`*_completed` pairs (and
`failed` if a block raises); `rec.diff(...)` builds a unified diff with `difflib`
and multiple diffs accumulate in the diff view. The SDK emits **bare canonical
envelopes**, so `intui watch` reads them with no adapter.
"""
