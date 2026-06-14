# in-TUI-tion quickstart

Two ways to use in-TUI-tion. Pick the one that matches you.

## Install

```sh
pip install in-tui-tion        # or: uv add in-tui-tion
```

Requires Python 3.11+ and a modern terminal (Windows Terminal, macOS
Terminal/iTerm2, common Linux/WSL terminals). The package ships inline types
(`py.typed`).

---

## Path A — stream-first (emit JSON, get a console)

If your tool already does the work (an agent, a CI job, a pipeline), you don't
write UI code — you **emit events** and let the kit render them. Emit JSON Lines
that follow the [event-stream contract](event-stream-contract.md):

```json
{"version":"1","event_id":"e1","run_id":"r1","timestamp":"2026-06-14T10:00:00Z","type":"task_started","scope":{"task_id":"build"},"summary":"Building"}
{"version":"1","event_id":"e2","run_id":"r1","timestamp":"2026-06-14T10:00:02Z","type":"task_completed","scope":{"task_id":"build"},"status":"passed"}
```

Then render a full console — **zero code**:

```sh
intui watch run.jsonl                 # replay a captured stream
intui watch -- my-agent --json        # spawn a producer, watch it live
```

Or from Python:

```python
from intui.console import watch

watch("run.jsonl")                    # a path, or any EventSource
```

You get a KITT activity strip, a conversation panel, and a routable central
view (`t` tasks, `l` lanes, `d` diff, `e` evidence) — public-safe by default
(`--no-public-safe` to show full diffs/evidence). The runner unwraps wrapped
records (`{"type":"run_trace_event","event":{…}}`) and ignores trailing
non-event records, so real producer output works out of the box. See the
[runner quickstart](../specs/009-console-runner/quickstart.md) for details.

Validate your stream first if you like:

```python
from intui.events import validate_stream
from intui.kit.state import KNOWN_EVENT_TYPES

for issue in validate_stream("run.jsonl", known_types=KNOWN_EVENT_TYPES):
    print(issue.line, issue.severity, issue.reason)
```

### Producer doesn't speak the canonical vocabulary? Use an adapter.

If your tool emits its own event names, a thin adapter normalizes them. The
built-in **IntentForge** adapter renders an `intentforge … --event-stream
ndjson` run with no IF-specific code:

```sh
intui watch --adapter intentforge run.ndjson           # replay a captured run
intui watch --adapter intentforge -- intentforge …     # watch a live run
```

```python
from intui.console import watch
from intui.adapters import IntentForgeSource

watch(IntentForgeSource("run.ndjson"))
```

See the [adapter quickstart](../specs/010-intentforge-adapter/quickstart.md).

---

## Path B — build in code

Compose the kit yourself. The smallest real app: a store with a reducer, a
bound widget, and a source.

```python
from intui.app import IntuiApp
from intui.events import Event, JsonlReplaySource
from intui.state import Snapshot, Store, compose_reducers
from intui.viewmodels import selector
from intui.widgets import BoundWidget

def log_reducer(lines, event):
    return (*lines, event.summary or event.type) if event.summary else lines

@selector
def log_vm(snapshot: Snapshot) -> tuple[str, ...]:
    return snapshot.slice("log")

class Log(BoundWidget):
    def render_view(self, vm): return "\n".join(vm) or "waiting…"

class MyApp(IntuiApp):
    def compose(self):
        yield Log(log_vm)

MyApp(
    store=Store(compose_reducers(log=(log_reducer, ()))),
    source=JsonlReplaySource("run.jsonl"),
).run()
```

For the full agentic console — modes, conversation, task chip/tree/lanes, diff
+ evidence, command palette, the KITT activity strip, a prompt — see
`examples/operator_console/` (the flagship). Smaller demos: `examples/
mission_control/` (the kit) and `examples/hello_replay/` (the foundation):

```sh
uv run python -m examples.operator_console
```

---

## Where things are

- **Event vocabulary** (the single source of truth): [event-stream contract](event-stream-contract.md)
- **Envelope schema**: [contracts/event-envelope.schema.json](contracts/event-envelope.schema.json)
- **Public API**: re-exported from `intui` (pipeline), `intui.kit` (components),
  `intui.kit.state` (engine-free models + selectors)
- **Principles**: `.specify/memory/constitution.md`
