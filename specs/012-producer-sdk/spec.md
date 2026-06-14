# Feature Specification: Producer SDK (emit)

**Feature Branch**: `012-producer-sdk`

**Created**: 2026-06-14

**Status**: Draft

**Input**: Strategy review — consuming a stream is toothbrush-easy (009/010), but
**producing** one still means hand-writing JSON envelopes. This feature is the
missing handle: a tiny, engine-free emitter so any Python tool produces canonical
events in a few lines, making "any tool → a console" true in both directions.

## Overview

Today a producer must hand-author envelopes (`version`, `event_id`, `run_id`,
`timestamp`, `scope`, `type`, …) and get the vocabulary right from a doc. That is
the opposite of stupid-easy and is the main thing standing between the project
and adoption.

The Producer SDK (`intui.emit`, re-exported from the engine-free `intui` root)
provides a `run_recorder(...)` that emits **valid canonical envelopes** to a
file, stdout, or a callable — with ergonomic helpers for the whole vocabulary and
context managers that auto-emit start/finish (and `failed` on exception). It also
builds unified diffs from before/after text (via `difflib`) so `file_diff` is a
one-liner.

The payoff — a live console from a ~15-line script, no JSON by hand:

```python
from intui import run_recorder
with run_recorder("run.ndjson") as rec, rec.run():
    with rec.task("build", "Build the app") as t:
        with t.work_item("compile"):
            rec.diff("src/app.py", before=old, after=new)
    rec.evidence(pass_rate="92%", certified="gold")
```

```sh
intui watch run.ndjson                      # replay it
intui watch -- python my_tool.py            # …or watch it live (emit to stdout)
```

The SDK emits **bare canonical envelopes** (the contract), so `intui watch` reads
them directly — no adapter needed. It is engine-free and headlessly testable.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Emit a run to a file in a few lines (Priority: P1)

A developer adds a few `run_recorder` calls to their tool, runs it, and gets a
`.jsonl` recording that `intui watch` renders — without writing any JSON or
knowing the envelope shape.

**Why this priority**: This is the keystone — it makes producing a stream as easy
as consuming one, and every other feature gets more valuable with more producers.

**Independent Test**: Record a run to a temp file with the SDK; read it back and
assert valid envelopes; reduce it through a store and assert the expected slices
(tasks, work items, diff, evidence).

**Acceptance Scenarios**:

1. **Given** `run_recorder(path)` and a few calls, **When** the run ends, **Then**
   the file contains one canonical envelope per line, each valid against the
   contract (no envelope errors vs `KNOWN_EVENT_TYPES`).
2. **Given** that file, **When** reduced through the bundled slices, **Then**
   tasks/work-items/diff/evidence appear as emitted.
3. **Given** `rec.diff(path, before=…, after=…)`, **When** emitted, **Then** it
   produces a `diff_ready` carrying a unified diff the kit parses into files.
4. **Given** `rec.evidence(pass_rate="92%", …)`, **When** emitted, **Then** it
   produces an `evidence_ready` with those metrics.

---

### User Story 2 - Watch a live run with no file (Priority: P1)

A developer emits to stdout and runs `intui watch -- python my_tool.py`; the
console updates live as the tool works, then reflects completion — no file, no
adapter, no JSON by hand.

**Why this priority**: The live "run your thing, see a console" loop is the
demo that sells the product, and it must need no glue.

**Independent Test**: Spawn a tiny SDK-based producer that emits to stdout; drive
it through the runner's subprocess source into a store; assert the events reduce
and the stream ends.

**Acceptance Scenarios**:

1. **Given** a recorder whose sink is stdout, **When** the tool emits, **Then**
   each event is a flushed ndjson line on stdout.
2. **Given** `intui watch -- <that tool>`, **When** it runs, **Then** the console
   reduces the emitted events live and reflects exit as stream end.
3. **Given** the SDK output, **When** validated, **Then** there are no envelope
   errors (bare canonical envelopes; no wrapper, no adapter needed).

---

### User Story 3 - Ergonomic lifecycle with context managers (Priority: P2)

A developer wraps work in `with rec.task(...)` / `with task.work_item(...)` and
the SDK emits the started/completed pair automatically — and marks `failed` if
the block raises.

**Why this priority**: Removes bookkeeping and makes the common case correct by
default (no forgotten completion; failures recorded).

**Independent Test**: Use the context managers around a block that succeeds and a
block that raises; assert the emitted started/completed(+status) events.

**Acceptance Scenarios**:

1. **Given** `with rec.task("t", "Title")`, **When** the block exits normally,
   **Then** `task_started` then `task_completed` (status completed) were emitted.
2. **Given** the block raises, **When** it exits, **Then** `task_completed` with
   `status: failed` was emitted and the exception propagates.
3. **Given** `with task.work_item("w")`, **Then** the work-item started/completed
   pair is emitted, scoped to the task.
4. **Given** `with rec.run()`, **Then** `run_started`/`run_completed` (or
   `run_failed`) bracket the block (driving the activity strip).

---

### Edge Cases

- A generic/unknown event type via `rec.emit("custom_thing", …)`: emitted as a
  valid envelope (open vocabulary), reduced as a pass-through by the kit.
- `rec.diff` with identical before/after: emits a `diff_ready` with no changes
  (empty diff) — no crash.
- Emitting after the recorder/file is closed: a clear error, not a corrupt file.
- Sequential calls from one thread: event ids stay unique and ordered.
- No sink given: defaults to stdout (the live-watch path).
- A callable sink that raises: surfaces to the caller (the SDK does not swallow).

## Requirements *(mandatory)*

### Functional Requirements

**Recorder + sinks**

- **FR-001**: The system MUST provide `run_recorder(sink=None, *, run_id=None,
  clock=None)` returning a recorder that emits canonical envelopes. `sink` MAY be
  a file path, a text file object, a callable taking the envelope mapping, or
  `None` (stdout). `run_id` defaults to a generated id; `clock` is injectable.
- **FR-002**: Every emitted event MUST be a complete, valid canonical envelope
  (`version="1"`, unique ordered `event_id`, the recorder's `run_id`, a
  `timestamp`, `type`, `scope`, optional `status`/`summary`/`payload`) — no
  envelope errors against `KNOWN_EVENT_TYPES`.
- **FR-003**: File/stdout sinks MUST write one JSON line per event and flush, so
  a live consumer sees events as they happen; the recorder MUST be usable as a
  context manager that closes a file sink.

**Vocabulary helpers**

- **FR-004**: The SDK MUST provide helpers covering the canonical vocabulary:
  tasks (created/started/blocked/completed), work items (started/completed),
  lanes/subagents (started/activity/completed), conversation (message/question/
  approval), artifacts (diff, evidence), view/mode, and run lifecycle, plus a
  generic `emit(type, …)` escape hatch for any (including custom) type.
- **FR-005**: `diff(path, *, before, after, public_safe=True)` MUST build a
  unified diff (stdlib `difflib`) and emit `diff_ready`; a `diff_unified(…)`
  variant MUST accept pre-built unified text.
- **FR-006**: `evidence(**metrics)` (and/or a metrics mapping) MUST emit
  `evidence_ready` with `{key,label,value}` metrics; `public_safe` defaults true.

**Ergonomic lifecycle**

- **FR-007**: Context managers `run()`, `task(id, title?)`, and
  `work_item(id, …)` MUST emit the started event on enter and the completed event
  on exit, emitting `status: failed` (or `run_failed`) when the block raises, and
  re-raising.
- **FR-008**: Work items created from a task handle MUST be scoped to that task
  (so they nest under it).

**Cross-cutting**

- **FR-009**: `intui.emit` MUST be engine-free (no Textual import; layering
  guard) and re-exported from the `intui` root so `from intui import
  run_recorder` works.
- **FR-010**: The SDK MUST emit **bare** canonical envelopes (no producer
  wrapper) so `intui watch` consumes them with no adapter.
- **FR-011**: A runnable example MUST demonstrate the SDK end-to-end (a script
  whose output is watchable live and as a file).

### Key Entities

- **RunRecorder**: the emitter — holds the run id, sink, id counter, clock;
  exposes vocabulary helpers + context managers.
- **Task / WorkItem handles**: context-manager objects that auto-emit start/finish
  and carry scope.
- **Sink**: file path / text file / callable / stdout; receives one envelope
  mapping (serialized to ndjson for file/stdout).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A ~15-line SDK script produces a recording that `intui watch`
  renders, with **no hand-written JSON** (verified headlessly + an example).
- **SC-002**: 100% of SDK-emitted events validate against `KNOWN_EVENT_TYPES`
  with zero envelope errors.
- **SC-003**: Emitting to stdout + `intui watch -- <script>` shows the run live
  and reflects exit (verified).
- **SC-004**: Context managers emit the correct started/completed pairs and
  `failed` on exception (verified).
- **SC-005**: `rec.diff(before, after)` yields a `diff_ready` the kit parses into
  the expected changed file(s) (verified).
- **SC-006**: `from intui import run_recorder` works and pulls in no terminal
  engine (layering guard green).

## Assumptions

- The SDK targets the **canonical** vocabulary (008); producer-specific shapes
  (e.g. IntentForge) remain the adapter's job (010).
- Python-first; the contract is language-agnostic JSON, so other-language
  emitters can follow later (out of scope here).
- Event ids are a per-recorder monotonic counter (deterministic, ordered);
  timestamps default to wall-clock UTC (injectable for deterministic tests).
- The SDK does not redact — producers own their data; the console redacts on
  display by default (Principle VI). `public_safe` flags are passed through.
