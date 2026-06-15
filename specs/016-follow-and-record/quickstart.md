# Quickstart: Live Follow & Record

## Follow a growing file

Point the console at a `.jsonl` file another process is still appending to:

```sh
intui watch --follow run.jsonl     # renders, then keeps updating; quit with q
```

```python
from intui.console import watch
watch("run.jsonl", follow=True)
```

It reads what's there, then tails new lines as they arrive (lines written in
pieces are parsed once they complete). The stream stays live until you quit.

`--follow` is for a file — combining it with a spawned command
(`intui watch --follow -- <cmd>`) is an error (a command is already live).

## Record the run you're watching

Press **`ctrl+s`** in the console to save the run so far to a canonical
`.jsonl` (`intui-recording-<timestamp>.jsonl` in the current directory). Replay
it any time:

```sh
intui watch intui-recording-20260614-1530.jsonl
```

Recorded files are **canonical** envelopes — even if you were watching an
adapted source (e.g. `--adapter intentforge`), the saved file replays with plain
`intui watch <file>` and no adapter. Great for sharing a run, filing a repro, or
turning a real run into a test fixture.

## Save a run from Python

```python
from intui.events import write_recording
write_recording("run.jsonl", app.store.events)   # the accepted events so far
```
