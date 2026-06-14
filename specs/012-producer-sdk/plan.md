# Implementation Plan: Producer SDK (emit)

**Branch**: `012-producer-sdk` | **Date**: 2026-06-14 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/012-producer-sdk/spec.md`

## Summary

A tiny, engine-free emitter that makes producing a canonical stream as easy as
consuming one. New module `intui.emit`:

- `run_recorder(sink=None, *, run_id=None, clock=None)` → a `RunRecorder` that
  serializes valid canonical envelopes to a file path, a text file, a callable,
  or stdout (default), one flushed ndjson line per event.
- Vocabulary helpers (`task_*`, `work_item_*`, `subagent_*`, `message`/`agent`/
  `user`/`system`, `question`, `approval`, `diff`/`diff_unified`, `evidence`,
  `view`/`mode`, `run_*`, `activity`) + a generic `emit(type, …)` escape hatch.
- Context-manager handles: `run()`, `task(id, title?)`, `Task.work_item(id, …)`
  emit started on enter, completed on exit, `failed` on exception, re-raising.
- `diff(path, before, after)` builds a unified diff via stdlib `difflib`.

Re-exported from the engine-free `intui` root (`from intui import run_recorder`).
Emits **bare** canonical envelopes so `intui watch` reads them with no adapter.
Ships an `examples/emit_demo` that is watchable live (`intui watch -- python -m
examples.emit_demo`) and as a file. Decisions in [research.md](research.md);
surface in [data-model.md](data-model.md) and
[contracts/contract-api.md](contracts/contract-api.md).

## Technical Context

**Language/Version**: Python 3.11–3.13 (unchanged).

**Primary Dependencies**: none new — stdlib `json`, `difflib`, `datetime`,
`contextlib`, `sys`. Reuses `intui.events.Event/Scope` for construction +
`to_mapping()` for serialization.

**Storage**: ndjson (the contract format).

**Testing**: pytest headless — emitted envelopes validate against
`KNOWN_EVENT_TYPES`; sinks (file/stdout/callable/list) capture lines; context
managers emit the right pairs incl. `failed`; `diff` builds parseable unified
text; reduce-through-a-store asserts slices; a spawned SDK producer → the 009
subprocess source → store (live path); root import stays engine-free.

**Target Platform**: unchanged (Windows/macOS/Linux/WSL).

**Project Type**: library + examples gallery (unchanged).

**Performance Goals**: O(1) per event; immediate flush for live consumers.

**Constraints**: `intui.emit` engine-free (lint + layering guard) and re-exported
from root; emits bare canonical envelopes (no wrapper); deterministic ids
(counter) + injectable clock for replayable tests.

**Scale/Scope**: one module + root re-export + an example + docs. Out of scope:
non-Python emitters, async/threaded emit, redaction in the SDK, a declarative
console *builder* (separate future slice).

## Constitution Check

| # | Principle | Status | Notes |
|---|-----------|--------|-------|
| I | Structured State | ✅ PASS | SDK only produces canonical events; all state still flows through store/reducers downstream. |
| II | Layered Architecture | ✅ PASS | `intui.emit` engine-free (stdlib + `intui.events`); root re-export stays Textual-free. |
| III | Actions Are Intents | ✅ PASS (n/a) | Production side; no UI intents. |
| IV | Keyboard-First | ✅ PASS (n/a) | No UI. |
| V | Meaningful Motion | ✅ PASS | `run()`/`activity()` emit the lifecycle that drives the strip. |
| VI | Public-Safe | ✅ PASS | SDK doesn't weaken safety; producers own data, console redacts on display; `public_safe` passed through. |
| VII | Test-First, Replayable | ✅ PASS | Headless test-first; deterministic ids + injectable clock. |
| VIII | Example-Driven | ✅ PASS | `examples/emit_demo`, watchable live + as a file (FR-011). |
| — | New deps justified | ✅ PASS | None. |

**Post-Phase-1 re-check (2026-06-14)**: no new deps; layering holds (emit imports
only stdlib + `intui.events`; root re-export adds no engine). GATE: PASS.

## Project Structure

```text
src/intui/
├── emit.py        # NEW — RunRecorder, Task/WorkItem handles, run_recorder(), sinks, diff()
└── __init__.py    # re-export run_recorder, RunRecorder (+ __all__)

examples/emit_demo/
├── __init__.py  __main__.py  app.py(or run.py)  README.md   # a watchable SDK producer

tests/
├── unit/
│   ├── test_emit.py            # envelopes valid; helpers; sinks; ids; diff/evidence; reduce-through
│   ├── test_emit_lifecycle.py  # context managers: started/completed pairs + failed on raise
│   └── test_layering.py        # (existing) root import stays engine-free (emit included)
└── integration or unit/
    └── test_emit_live.py       # spawn SDK producer -> SubprocessSource -> store (live path)

docs/quickstart.md  # + an "emit" path (produce a stream in a few lines)
README.md           # + the run_recorder one-liner
```

**Structure Decision**: a single engine-free `intui.emit` module reusing the
existing `Event`/`Scope` for construction and `to_mapping()` for serialization;
re-exported from the root for one-import ergonomics; an example that doubles as
the live-watch demo.

## Complexity Tracking

No constitutional violations — table intentionally empty.
