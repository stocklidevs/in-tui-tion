# Data Model: Producer SDK (emit)

**Feature**: `012-producer-sdk` | **Date**: 2026-06-14

No new event types or snapshot shapes — the SDK *produces* the existing canonical
envelopes (008). This documents the new runtime objects in `intui.emit`.

## `run_recorder` factory

```text
run_recorder(
    sink: Path | str | TextIO | Callable[[Mapping[str, Any]], None] | None = None,
    *,
    run_id: str | None = None,        # default: generated "run-<short>"
    clock: Callable[[], datetime] | None = None,   # default: datetime.now(UTC)
) -> RunRecorder
```

Sink resolution:

| `sink` | behavior |
|---|---|
| `None` | write ndjson + flush to `sys.stdout` (the live-watch path) |
| `Path`/`str` | open the file (newline `\n`) and write ndjson + flush per event; closed on recorder close |
| text file object | write ndjson + flush per event (not closed by the recorder) |
| callable | called with each envelope **mapping** (no serialization) |

## `RunRecorder`

Holds `run_id`, the resolved sink, an `event_id` counter, and the clock.

Generic escape hatch:

```text
emit(type: str, *, task_id=None, work_item_id=None, lane_id=None, session_id=None,
     status=None, summary=None, **payload) -> Event
```

Builds + emits a canonical `Event` (auto `version`/`event_id`/`run_id`/`timestamp`),
returns it (handy for tests).

Vocabulary helpers (all thin wrappers over `emit`):

| method | emits | notes |
|---|---|---|
| `task_created/started/blocked(task_id, title=None, summary=None)` | `task_*` | `title`→payload `name` |
| `task_completed(task_id, *, status="passed", summary=None)` | `task_completed` | `status` failed→failed |
| `work_item_started(work_item_id, *, task_id=None, title=None)` | `work_item_started` | |
| `work_item_completed(work_item_id, *, task_id=None, status="passed")` | `work_item_completed` | |
| `subagent_started/activity/completed(lane_id, …)` | `subagent_*` | lane/worker |
| `message(role, text)`, `agent(text)`, `user(text)`, `system(text)` | `message_added` | |
| `question(text)`, `approval(text)` | `question_requested`/`approval_requested` | |
| `diff(path, *, before, after, public_safe=True)` | `diff_ready` | unified via `difflib` |
| `diff_unified(unified, *, title="diff", public_safe=True)` | `diff_ready` | pre-built text |
| `evidence(*, title="evidence", public_safe=True, **metrics)` | `evidence_ready` | metrics→`[{key,label,value}]` |
| `view(view)`, `mode(mode)` | `view_selected`/`mode_changed` | |
| `activity(state)` | `activity_set` | drives the strip |
| `run_started()`, `run_completed(status="passed")`, `run_failed()` | run lifecycle | conventions |

Context managers:

```text
run() -> ContextManager            # run_started on enter; run_completed / run_failed on exit
task(task_id, title=None) -> Task   # task_started on enter; task_completed (failed on raise) on exit
```

Recorder is itself a context manager (`__enter__`/`__exit__`) closing a file sink.

## `Task` / `WorkItem` handles

```text
Task.work_item(work_item_id, title=None) -> WorkItem   # context manager
Task.note(text) / Task.diff(...) / Task.evidence(...)  # convenience, scoped to the task
WorkItem: context manager — work_item_started on enter; work_item_completed
          (failed on raise) on exit; scoped to the parent task id.
```

On `__exit__` with an exception: emit the completed event with `status="failed"`
(or `run_failed`) and re-raise.

## Serialization

`json.dumps(event.to_mapping())` + `"\n"`, flushed, for file/stdout sinks. A
callable sink receives `event.to_mapping()` directly. Bare canonical envelopes —
no wrapper (D4) — so `intui watch <file>` / `intui watch -- <tool>` consume them
with no adapter.

## What does NOT change

- Event envelope, store, reducers, selectors, widgets, the contract vocabulary.
  The SDK is pure construction + serialization over existing types, re-exported
  from the engine-free root.
