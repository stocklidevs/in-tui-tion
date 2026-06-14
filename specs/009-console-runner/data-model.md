# Data Model: Zero-Config Console Runner

**Feature**: `009-console-runner` | **Date**: 2026-06-14

No new event envelope or snapshot shapes are introduced — the runner consumes
the **canonical** vocabulary (feature 008) and renders the **existing** view
models (002/004/005/007). This documents the new runtime objects (sources, app,
factory) and the promoted run-status slice.

## Stream sources (engine-free, `intui.events.sources`)

### `NdjsonStreamSource`

An `EventSource` over newline-delimited JSON.

```text
NdjsonStreamSource(
    lines: Path | str | Iterable[str] | AsyncIterable[str],
    *,
    event_record_types: tuple[str, ...] = (),   # record `type`s to unwrap
    rate: float | None = None,                   # pacing for finite line iterables/files
)
```

Per non-blank line:

| Input record | Behavior |
|---|---|
| A bare envelope object `{version, event_id, …, type, …}` | yielded as-is (raw mapping). |
| A wrapped record `{"type": R, "event": {…envelope…}}` where `R ∈ event_record_types` | the inner `event` mapping is yielded. |
| A record whose `type` is **not** in `event_record_types` and that has no envelope fields (e.g. `{"type":"summary",…}`) | ignored (non-event). |
| Invalid JSON / not an object | yields `{"__malformed__": <reason>, "line_number": N}` (store records it in health). |

Mirrors `validate_stream`'s unwrap/ignore semantics (008) so the same producer
output validates and renders.

### `SubprocessSource`

An `EventSource` that spawns a command and reads its stdout ndjson.

```text
SubprocessSource(
    cmd: Sequence[str],                          # argv (no shell)
    *,
    event_record_types: tuple[str, ...] = (),
)
```

- Spawns via `asyncio.create_subprocess_exec(*cmd, stdout=PIPE, stderr=…)`.
- Decodes stdout line-by-line through the same logic as `NdjsonStreamSource`.
- Child stdout EOF → iterator stops → `Store.run` marks the stream **ENDED**.
- A spawn failure (e.g. `FileNotFoundError` for an unknown command) raises out
  of `__aiter__`; `Store.run` marks **DISCONNECTED**; the CLI converts a
  pre-launch failure into a clear message + non-zero exit.

Both sources satisfy the existing `EventSource` Protocol and need no store
changes.

## Run-status slice (promoted to `intui.kit.state.run_status`)

```text
RUN_STATUS_EVENT_TYPES: frozenset[str]   # the lifecycle types the reducer reads
run_status_slice() -> tuple[Reducer, str]   # (run_status_reducer, "idle")
```

`run_status_reducer(status: str, event: Event) -> str` maps lifecycle +
synthetic events to the R6 activity states already defined in
`intui.kit.state.activity` (`ACTIVITY_STATES`):

| Event type | Resulting state |
|---|---|
| `activity_set` (payload `state`) | that explicit state |
| `run_started`, `task_started`, `subagent_started` | `thinking` |
| `task_blocked` | `waiting` |
| `gate_started` | `verifying` |
| `run_failed` | `failure` |
| `run_completed` | `passed` |
| (anything else) | unchanged |

`RUN_STATUS_EVENT_TYPES` is unioned into `KNOWN_EVENT_TYPES`, so these lifecycle
types become part of the documented contract (drift-proof — the reducer reads
the constant).

## `ConsoleApp` (rendering layer, `intui.console.app`)

`ConsoleApp(IntuiApp)` — a batteries-included viewer. Constructed with a store
(canonical slices) and an `EventSource`; composes:

```text
Header
ActivityStrip(activity_state, swoosh_glow=…, sweep_seconds=…)   # R6, driven by run_status slice
Horizontal #body:
    VerticalScroll #conversation-col: ConversationLog(conversation_view())
    ViewRouter(view_router_view(), views={
        tasks:    VerticalScroll(TaskCounterChip, TaskTree),
        lanes:    LanesPanel(lanes_view()),
        diff:     DiffViewer(diff_view(public_safe=…)),
        evidence: EvidencePanel(evidence_view(public_safe=…)),
    })
CommandBar(view actions + palette)
Footer
```

Intents: `select_view` → `view_selected` event → state (reusing the established
handler). No modes, no prompt (D5). Public-safe threaded into the diff/evidence
selectors (D8).

### `build_console(...)` factory

```text
build_console(
    source: EventSource,
    *,
    public_safe: bool = True,
    sweep_seconds: float = 1.6,
) -> ConsoleApp
```

Builds the store with the canonical slices:
`views`, `conversation`, `taskboard`, `artifacts`, `run_status` (no `modes`),
wires the source, and returns the app.

### `watch(...)` one-liner (`intui.console.runner`)

```text
watch(
    source: EventSource | Path | str,
    *,
    public_safe: bool = True,
    rate: float | None = None,
) -> None
```

- A `Path`/`str` ending in a stream file → wrapped in `NdjsonStreamSource`
  (with `event_record_types=("run_trace_event",)` so real producer output works
  out of the box) and the given `rate`.
- An `EventSource` → used directly.
- Builds via `build_console` and calls `.run()`.

## CLI surface (`intui.console.cli`)

```text
intui watch [--public-safe | --no-public-safe] [--rate R] <file.jsonl>
intui watch [--public-safe | --no-public-safe] -- <command> [args…]

main(argv: list[str] | None = None) -> int   # 0 ok; non-zero on bad input
```

- File form → `NdjsonStreamSource(path, event_record_types=("run_trace_event",),
  rate=R)`.
- `-- cmd…` form → `SubprocessSource(cmd, event_record_types=("run_trace_event",))`.
- Missing file / uncstartable command → `error: …` on stderr, non-zero exit (no
  traceback).
- Wired as `[project.scripts] intui = "intui.console.cli:main"`.

## What does NOT change

- Event envelope, `Store`, `EventStream`/health, snapshots, selectors, and all
  existing widgets are unchanged. The runner is pure composition + two new
  sources + one promoted slice + a CLI.
