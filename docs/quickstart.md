# in-TUI-tion quickstart

Two ways to use in-TUI-tion. Pick the one that matches you.

## Install

```sh
pip install intui        # or: uv add intui
```

Requires Python 3.11+ and a modern terminal (Windows Terminal, macOS
Terminal/iTerm2, common Linux/WSL terminals). The package ships inline types
(`py.typed`).

---

## Path A — stream-first (emit events, get a console)

If your tool already does the work (an agent, a CI job, a pipeline), you don't
write UI code — you **emit events** and let the kit render them.

### Easiest: the Producer SDK (no JSON by hand)

```python
from intui import run_recorder

with run_recorder("run.ndjson") as rec, rec.run():
    with rec.task("build", "Build the app") as build:
        with build.work_item("compile"):
            rec.diff("src/app.py", before=old, after=new)
    rec.evidence(pass_rate="92%", certified="gold")
```

```sh
intui watch run.ndjson                 # replay it
intui watch -- python my_tool.py       # …or watch it live (emit to stdout)
```

The context managers auto-emit the started/completed pairs (and `failed` on
exception); `rec.diff(...)` builds a unified diff and many diffs accumulate;
`rec.file_written(...)` populates a **files** view (press `f` for the workspace
tree — see the [file-tree quickstart](../specs/013-workspace-file-tree/quickstart.md)).
In that view, `o`/`c`/`x` **request** open/copy/delete as intents your app
fulfills (delete is confirmed; the library never touches disk —
[file-actions quickstart](../specs/014-file-actions-intents/quickstart.md)). See
the [emit quickstart](../specs/012-producer-sdk/quickstart.md).

### Or write the JSON Lines yourself

Emit lines that follow the [event-stream contract](event-stream-contract.md):

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

You get a KITT activity strip over a single-column run timeline with a
bottom-pinned prompt; `d`/`/diff` unfolds the diff inline and `t/l/f/e/m`
(or `/tasks` … from the prompt) open panels as overlays — public-safe by default
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

### Time-travel through a run

In the console, `space` pauses/resumes, `,`/`.` step back/forward one event,
`home` rewinds to the start, `end` resumes to live. Every panel shows the run
*as it was* at that point (it's just `reduce(events[:n])`). See the
[scrubber quickstart](../specs/017-time-travel-scrubber/quickstart.md).

### Watch your pytest run

```sh
pytest --intui=run.jsonl     # the bundled plugin emits a stream as tests run
intui watch run.jsonl        # tests as tasks/work items, failures, a summary
```

Inert unless you pass `--intui`. See the
[pytest quickstart](../specs/019-pytest-plugin/quickstart.md).

### Follow a growing file, and record what you watch

```sh
intui watch --follow run.jsonl     # tail a file another process is writing
```

Press `ctrl+s` in the console to save the run so far to a canonical
`intui-recording-<timestamp>.jsonl` you can replay later (even an adapted run
saves as canonical — replays with no adapter). See the
[follow & record quickstart](../specs/016-follow-and-record/quickstart.md).

### Watch a command's resources

```sh
pip install "intui[metrics]"            # adds psutil
intui watch --metrics -- python build.py      # press `m` for CPU/memory/status
```

See the [metrics quickstart](../specs/015-process-metrics-monitor/quickstart.md).

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
