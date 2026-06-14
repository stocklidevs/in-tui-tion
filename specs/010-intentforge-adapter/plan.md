# Implementation Plan: IntentForge Adapter

**Branch**: `010-intentforge-adapter` | **Date**: 2026-06-14 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/010-intentforge-adapter/spec.md`

## Summary

A thin normalizer that turns IntentForge's run-trace ndjson into the canonical
in-TUI-tion vocabulary so feature 009's runner renders a real IF run with no
IF-specific code in the console/kit. Three pieces:

1. A **pure, engine-free `adapt_record(record, *, run_id)`** in a new
   `intui.adapters.intentforge` module: maps each IF record
   (`{sequence,name,payload}`, wrapped or bare) and the trailing `summary` to a
   canonical `Event`, or `None` for an unknown/ignored record. Per the verified
   mapping table in the spec.
2. An **`IntentForgeSource`** (`EventSource`) that reads IF ndjson from a
   file/line-iterable (replay) or a spawned subprocess (live) and yields adapted
   canonical envelopes — including the summary. It reuses 009's line-reading
   helpers (a small refactor extracts subprocess line-reading so both sources
   share it).
3. An **`--adapter intentforge`** switch on `intui watch` selecting the adapter
   for both the file and `-- <cmd>` forms.

Plus a runnable **example** (`examples/intentforge_console`) over a committed
IF-shaped fixture. Decisions in [research.md](research.md); shapes in
[data-model.md](data-model.md); surface in
[contracts/contract-api.md](contracts/contract-api.md).

## Technical Context

**Language/Version**: Python 3.11–3.13 (unchanged).

**Primary Dependencies**: Textual 6.x (runtime, unchanged). **No new deps** — the
adapter is stdlib `json`/`datetime`. IntentForge is NOT a dependency: the adapter
only understands IF's on-the-wire JSON (loose coupling); the IF repo is read-only
reference.

**Storage**: JSONL/ndjson (unchanged).

**Testing**: pytest headless for `adapt_record` (per-event mapping, summary,
edge cases, validator round-trip against `KNOWN_EVENT_TYPES`) and
`IntentForgeSource` (file fixture + a tiny spawned IF-shaped producer); Pilot for
the example rendering through `ConsoleApp`; a CLI test for `--adapter intentforge`
arg wiring.

**Target Platform**: Windows/macOS/Linux/WSL (subprocess via `create_subprocess_
exec`; tests spawn `sys.executable -c …`).

**Project Type**: library + examples gallery (unchanged).

**Performance Goals**: adapter is O(1) per record; live ingestion stays
non-blocking (reuses 009's async worker).

**Constraints**: `adapt_record` + `IntentForgeSource` engine-free (lint ban +
layering guard); adapter emits only canonical types (validator clean); public-
safety preserved (forwards IF's already-redacted diffs; default-on redaction
unchanged).

**Scale/Scope**: one adapter module + source + CLI switch + example + fixture.
Out of scope: changing the kit/contract, vendoring IF, mapping IF subcommands
that don't emit this record shape, richer summary metrics beyond the recognized
top-level keys.

## Constitution Check

| # | Principle | Status | Notes |
|---|-----------|--------|-------|
| I | Structured State | ✅ PASS | Adapter only produces canonical events; all state still flows through the store/reducers. |
| II | Layered Architecture | ✅ PASS | Adapter + source engine-free in `intui.adapters`; no Textual import; CLI switch in `intui.console` (rendering layer). |
| III | Actions Are Intents | ✅ PASS (n/a) | No new actions. |
| IV | Keyboard-First, Accessible | ✅ PASS (n/a) | Reuses the 009 console's navigation. |
| V | Meaningful Motion | ✅ PASS | Matrix lifecycle → run-status drives the activity strip with real state. |
| VI | Public-Safe | ✅ PASS | Forwards IF's redacted diffs; introduces no paths/secrets; console redaction stays default-on (FR-008). |
| VII | Test-First, Replayable | ✅ PASS | Pure adapter + source headless test-first; deterministic synthetic timestamps keep replays deterministic. |
| VIII | Example-Driven | ✅ PASS | Ships `examples/intentforge_console` + a committed IF fixture (FR-011). |
| — | New deps justified | ✅ PASS | None — stdlib only; IF not imported. |

**Post-Phase-1 re-check (2026-06-14)**: no new deps; layering holds (adapter
imports only `intui.events` envelope types + stdlib). GATE: PASS — Complexity
Tracking empty.

## Project Structure

### Documentation (this feature)

```text
specs/010-intentforge-adapter/
├── plan.md  research.md  data-model.md  quickstart.md
├── contracts/contract-api.md
├── checklists/requirements.md
└── tasks.md (Phase 2 via /speckit-tasks)
```

### Source / repo changes

```text
src/intui/
├── adapters/                 # NEW engine-free subpackage
│   ├── __init__.py           # export adapt_record, IntentForgeSource
│   └── intentforge.py        # adapt_record(), IF name->canonical mapping, IntentForgeSource
├── events/
│   └── sources.py            # refactor: extract _aiter_subprocess_lines (shared by
│                             #   SubprocessSource + IntentForgeSource); no behavior change
└── console/
    └── cli.py                # + --adapter {none,intentforge}; wrap source when intentforge

examples/intentforge_console/
├── __init__.py  __main__.py  app.py   # render the IF fixture through the adapter + ConsoleApp
├── run.ndjson                          # committed IF-shaped fixture (wrapper lines + summary)
└── README.md

tests/
├── unit/
│   ├── test_adapter_intentforge.py    # per-event mapping, summary, edge cases, validator round-trip
│   ├── test_intentforge_source.py     # file fixture + spawned IF-shaped producer -> store
│   └── test_console_cli.py            # (extend) --adapter intentforge wiring
└── integration/
    └── test_intentforge_console.py    # Pilot: fixture renders tasks/work-items/diff/evidence
```

**Structure Decision**: a new engine-free `intui.adapters` subpackage holds the
pure normalizer and its source (so adapters are a first-class, layering-guarded
home for future producers); the only rendering-layer change is the `intui watch`
`--adapter` switch. SubprocessSource's line-reading is extracted into a shared
helper so `IntentForgeSource` reuses it without duplication.

## Complexity Tracking

No constitutional violations — table intentionally empty.
