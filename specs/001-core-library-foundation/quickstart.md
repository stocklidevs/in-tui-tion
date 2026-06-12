# Quickstart: Core Library Foundation

**Feature**: `001-core-library-foundation` | **Date**: 2026-06-12

How a developer goes from fresh checkout to the running example in under 10
minutes (SC-001), and how to use the library in their own app.

## Prerequisites

- Python 3.11+ available, or just [uv](https://docs.astral.sh/uv/) (uv can
  install Python itself)
- A modern terminal: Windows Terminal, macOS Terminal/iTerm2, or a common
  Linux/WSL terminal

## Run the example

```sh
git clone <repo-url> in-tui-tion
cd in-tui-tion
uv sync                                  # creates venv, installs intui + dev deps
uv run python -m examples.hello_replay   # launches the example TUI
```

The example replays `examples/hello_replay/recording.jsonl` — a simulated
multi-step run — and demonstrates:

- a **Signal** status indicator (color + motion + glyph) driven by the
  replayed run's status: swoosh while working, amber pulse while waiting,
  green steady on success, red strobe on failure
- a scrolling item list derived from events via view models
- **theme switching** (`t` key) with no widget code involved
- a normal intent (`r` — re-run replay) and a **risky intent**
  (`x` — clear history) that requires confirmation before delivery
- stream-health display when the recording ends

Everything is keyboard-operable; press `?` for bindings.

## Run the tests

```sh
uv run pytest                  # headless: unit + replay determinism + Pilot tests
uv run pytest tests/replay     # just the recorded-fixture determinism suite
```

No terminal emulator is required — core pipeline tests import no Textual.

## Use the library in your own app

```python
from intui.events import Event, JsonlReplaySource, parse_event
from intui.state import Store, compose_reducers
from intui.viewmodels import selector
from intui.actions import Intent
from intui.app import IntuiApp

# 1. Reduce events into your state slice (pure; unknown types pass through)
def tasks_reducer(tasks, event):
    if event.type == "task_completed":
        return tasks.with_done(event.scope.task_id)
    return tasks

# 2. Project state into what your widgets show
@selector
def task_counter(snapshot):
    t = snapshot.slice("tasks")
    return f"{t.done} / {t.total} tasks complete"

# 3. Handle user intents by appending new events — never by mutating state
async def on_intent(intent: Intent):
    if intent.name == "retry":
        ...  # append events to your source

# 4. Wire it up
store = Store(compose_reducers(tasks=tasks_reducer))
app = MyApp(  # subclass of IntuiApp; compose() places BoundWidget/Signal
    store=store,
    source=JsonlReplaySource("recording.jsonl"),
    on_intent=on_intent,
)
app.run()
```

## Record and replay

```python
from intui.events import write_recording, read_recording

write_recording("session.jsonl", events)      # one JSON envelope per line
events = read_recording("session.jsonl")      # lossless round-trip
```

Replaying the same recording always produces an identical final snapshot —
that's the backbone of the test suite, and the recommended way to capture a
bug: save the stream that triggers it, commit it as a fixture under
`tests/replay/`.
