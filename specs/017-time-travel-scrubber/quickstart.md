# Quickstart: Time-Travel Scrubber

Step through a run inside the console — pause, rewind, replay.

## In the console

While watching (a replay or a live run):

- **`space`** — pause / resume (live)
- **`,`** — step back one event
- **`.`** — step forward one event
- **`home`** — jump to the start
- **`end`** — resume to live

A status line shows where you are: `▶ live · 47 events` or `⏸ 12 / 47`. While
paused on a live run, the view stays frozen at your point while the total keeps
climbing; press `end` to jump back to the latest.

Every panel (tasks, diff, files, metrics, conversation) shows the run **as it
was** at the cursor — because each historical state is just the reduction of the
events up to that point.

## Reconstruct a past state in code

```python
snap_at_10 = app.store.snapshot_at(10)     # state after the first 10 events
latest = app.store.snapshot_at(len(app.store.events))   # == live state
```

```python
from intui.state import Timeline

tl = Timeline()                 # live
tl = tl.pause(total=47)         # freeze at 47
tl = tl.step(-1, total=47)      # -> 46
tl = tl.to_start()              # -> 0
tl = tl.to_end()                # live again
pos = tl.position(total=47)
```

Scrubbing is pure inspection — it never changes the run or stops ingestion; live
events keep arriving in the background while you look around.
