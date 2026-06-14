# Research & Decisions: Zero-Config Console Runner

**Feature**: `009-console-runner` | **Date**: 2026-06-14

Each decision records what was chosen, why, and the alternatives rejected.

## D1 — Live input: spawned subprocess + file, NOT piped stdin

**Decision**: Live watching spawns a user-provided command
(`intui watch -- <cmd>`) and reads its **stdout**; the other mode replays a
`.jsonl` **file**. We do **not** read events from the terminal's stdin pipe.

**Why**: A full-screen Textual app owns the terminal — it needs stdin for its
own keyboard input. Consuming a `program | intui watch` pipe would fight the
TUI for the same fd and break keyboard navigation. Spawning the producer
ourselves lets the console keep the keyboard while reading the child's stdout
through a separate pipe (FR-010). It is also the better UX: one command runs
your thing *and* shows the console.

**Alternatives rejected**: (a) stdin pipe — breaks the TUI's keyboard, the
classic mistake. (b) a socket/port — heavier, needs a protocol, overkill for the
toothbrush case. (c) require the producer to write a file then replay — loses
"live."

## D2 — `NdjsonStreamSource` over an abstract line iterable

**Decision**: `NdjsonStreamSource` takes either a file path or any
(sync or async) iterable of text lines, plus `event_record_types` (record
`type`s to unwrap, e.g. `"run_trace_event"`) and treats any other top-level
record as a non-event and ignores it. It yields raw envelope mappings; malformed
lines yield the same `{"__malformed__": …}` shape `JsonlReplaySource` uses so the
store surfaces them through health.

**Why**: One ndjson parser, two front ends (file + live pipe). Unwrapping and
non-event ignoring match exactly what `validate_stream` already does (008) and
what IntentForge emits (`{"type":"run_trace_event","event":{…}}` + a trailing
`{"type":"summary",…}`), so the runner consumes real producer output without a
shim. Reusing the `__malformed__` convention reuses the store's existing health
path — no new failure plumbing.

**Alternatives rejected**: (a) extend `JsonlReplaySource` with unwrap flags —
muddies the file-only replayer; a dedicated source is clearer and composes with
the subprocess pipe. (b) make unwrapping the store's job — that would push
producer-specific framing into the engine; keep it at the edge.

## D3 — `SubprocessSource` via `asyncio.create_subprocess_exec`

**Decision**: `SubprocessSource(cmd: Sequence[str])` spawns with
`asyncio.create_subprocess_exec(*cmd, stdout=PIPE)` (no shell), reads stdout
line-by-line, and feeds each line through the same ndjson decode/unwrap logic as
D2. Source exhaustion = child stdout EOF → natural stream end; a spawn failure
(`FileNotFoundError`) raises out of `__aiter__` and is surfaced by `Store.run`
as DISCONNECTED, with the CLI translating a pre-launch failure into a clear
message + non-zero exit.

**Why**: `create_subprocess_exec` is non-blocking and integrates with Textual's
asyncio loop, so ingestion never blocks rendering (FR-009). No shell avoids
quoting/injection surprises and is portable; the user supplies argv. Tests spawn
`sys.executable -c "<prints ndjson>"` — portable across OSes, no fixture binary.

**Alternatives rejected**: (a) `subprocess.Popen` + a reader thread — works but
re-introduces threading we don't need given the event loop. (b) `shell=True` —
quoting/security footgun; the `--` argv form is cleaner.

## D4 — Promote the run-status reducer into `intui.kit.state`

**Decision**: Move the lifecycle→activity-state mapping (currently
`run_status_reducer` in the `operator_console` example) into engine-free
`intui.kit.state.run_status` as `run_status_slice()` returning
`(reducer, "idle")`, with a declared `RUN_STATUS_EVENT_TYPES` unioned into
`KNOWN_EVENT_TYPES`. Refactor the flagship to import it (no behavior change).

**Why**: `ConsoleApp` must drive the KITT strip with **no application code**;
the mapping is generic (run_started/task_started→thinking, gate_started→
verifying, run_failed→failure, run_completed→passed, …) and belongs with the
other canonical slices. Promoting it also makes the activity vocabulary part of
the documented contract (drift-proof via the union) and lets the example dedupe.

**Alternatives rejected**: (a) keep it in the example and copy into ConsoleApp —
duplication, drift risk, and the activity event types stay outside
`KNOWN_EVENT_TYPES`. (b) bake the mapping into the ActivityStrip widget — that
would put reducer logic in the rendering layer (Principle II violation).

## D5 — `ConsoleApp` is a read-mostly viewer (no modes, no prompt)

**Decision**: The batteries-included console renders activity strip +
conversation + a routable central view (tasks/lanes/diff/evidence) + command bar
(view actions + palette) + footer. It deliberately omits modes and the prompt
input. The full interactive operator console (modes + prompt + scripted replies)
stays the flagship **example**.

**Why**: The generic substrate the market lacks is a *viewer*: point it at any
compliant stream and navigate. Modes are an opinionated workflow overlay and the
prompt implies a live agent to talk back to — neither is meaningful for an
arbitrary producer/replay. Keeping the default lean is the toothbrush principle;
the example shows the maximal composition for those who want it.

**Alternatives rejected**: (a) include modes/prompt — couples the generic viewer
to an agent-console workflow and confuses "watch a CI job." (b) make every panel
configurable up front — premature; sensible fixed defaults first, knobs later.

## D6 — Surface lives in `intui.console`, not the engine-free root

**Decision**: `ConsoleApp`, `watch`, and `build_console` are exported from
`intui.console`; they are **not** re-exported from the `intui` root. The CLI is
`intui.console.cli:main`.

**Why**: Importing `intui` must stay Textual-free (Principle II; enforced by the
layering guard and the root re-export test). `ConsoleApp` imports Textual + the
kit, so it can only live below the root. `from intui.console import watch` is
still a one-liner and keeps the simple story.

**Alternatives rejected**: re-export from root for ergonomics — would pull
Textual into the engine-free import and break the layering guarantee.

## D7 — CLI via stdlib `argparse`, errors as messages not tracebacks

**Decision**: `intui watch [--public-safe/--no-public-safe] [--rate R]
(<file.jsonl> | -- <cmd…>)` implemented with `argparse`; `main(argv)` returns an
int exit code. A missing/unreadable file and a command that cannot start produce
a one-line `error: …` on stderr and a non-zero exit, not a traceback.

**Why**: No new dependency; `argparse` handles `--` passthrough for the command
form. Returning an int from `main([...])` makes the parse + error paths unit
testable without spawning a process or a terminal. Clear errors are an explicit
success criterion (SC-005).

**Alternatives rejected**: (a) `click`/`typer` — a new dependency for one
command. (b) let exceptions propagate — fails SC-005.

## D8 — Public-safe wiring through existing selector flags

**Decision**: `build_console(..., public_safe: bool = True)` threads the flag
into `diff_view(public_safe=…)` and `evidence_view(public_safe=…)`; the CLI's
`--no-public-safe` sets it false. Redaction otherwise is unchanged from 004.

**Why**: The selectors already take a `public_safe` parameter and default-on
redaction is already implemented (004) — the runner only needs to expose the
toggle, not re-implement safety. Default stays True (Principle VI).

**Alternatives rejected**: a new redaction layer — duplicative; reuse 004.

## Open questions / deferred

- **IntentForge vocabulary** (`case_started`, `file_diff`, …) is normalized by
  the **feature-010 adapter**; this runner consumes the canonical vocabulary and
  is demoed against a canonical fixture. Not in scope here.
- **`--follow`** (tail a growing file) and **attach-to-PID** are deferred; file
  replay + subprocess spawn cover the toothbrush case.
