# Implementation Plan: Core Library Foundation

**Branch**: `001-core-library-foundation` | **Date**: 2026-06-12 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/001-core-library-foundation/spec.md`

## Summary

Build the foundation layer of the in-TUI-tion library: a versioned,
append-only event pipeline (events → reducers → immutable state snapshots →
memoized view models), a state-driven component model with intent-based input
and confirmation for risky actions, token-based theming with one data-driven
Signal primitive, JSONL recording/replay, and one runnable example
(`hello_replay`) demonstrating it all. Technical approach (per
[research.md](research.md)): pure-Python, engine-agnostic pipeline core with
zero terminal dependencies, rendered through Textual 6.x via a thin reactive
bridge; tested headlessly with pytest plus Textual's Pilot/snapshot tooling.

## Technical Context

**Language/Version**: Python 3.11–3.13

**Primary Dependencies**: Textual 6.x (terminal engine; widget/app layer
only — the pipeline core imports no Textual). Dev: pytest, pytest-asyncio,
pytest-textual-snapshot, ruff, mypy.

**Storage**: JSON Lines (`.jsonl`) files for event-stream recordings; no
database.

**Testing**: pytest for headless pipeline tests (unit + replay fixtures);
Textual `Pilot` for headless app/interaction tests; `pytest-textual-snapshot`
for visual regression.

**Target Platform**: Common modern terminals on Windows, macOS, Linux, WSL.

**Project Type**: Library (src layout) with runnable examples gallery.

**Performance Goals**: UI remains responsive (renders coalesce, input
accepted) while ingesting ≥100 events/second over a 1,000+ event stream
(SC-003); replay of identical streams is deterministic byte-for-byte at the
snapshot level (SC-002).

**Constraints**: Pipeline core MUST be importable and testable with no
terminal attached (FR-005); rendering MUST NOT block on ingestion (FR-012);
graceful degradation on resize/reduced color (FR-013); append-only,
deduplicated event streams (FR-002).

**Scale/Scope**: Foundation layer only — pipeline, component model bridge,
intents, theming, one Signal primitive, one example. Component kit widgets,
agentic console, IntentForge adapter, and live external sources are later
features (source interface designed to admit them).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| # | Principle | Status | Notes |
|---|-----------|--------|-------|
| I | Structured State, Not Raw Logs | ✅ PASS | The feature *is* the pipeline: append-only versioned events → reducer → snapshot → view models → widgets. Widgets bind to view models only (FR-010). |
| II | Layered Architecture | ✅ PASS | Only the core layer plus one example. Core has no app knowledge; example uses only the public API. Pipeline subpackages additionally import no Textual, keeping the engine at the edge of the core itself. |
| III | Actions Are Intents | ✅ PASS | All input surfaces as named Intent objects to an app handler; risky intents require confirmation (FR-014/016). No library-side state mutation. |
| IV | Keyboard-First, Accessible | ✅ PASS | Keybindings first, mouse supplements (FR-015); every color-coded status has a textual/symbolic counterpart (FR-018, SC-006). |
| V | Meaningful Motion | ✅ PASS | One Signal primitive, fully data-driven from bound state fields; no decorative-only effects shipped. |
| VI | Public-Safe by Default | ✅ PASS (scoped) | Foundation carries `public_safe` metadata through the pipeline untouched; enforcement lives in future evidence-rendering components (spec Assumptions). |
| VII | Test-First and Replayable | ✅ PASS | Headless pipeline tests with recorded JSONL fixtures are the primary test vehicle (SC-005); tasks will order tests before implementation. |
| VIII | Example-Driven | ✅ PASS | `examples/hello_replay` exercises every shipped capability and runs from fresh checkout (FR-019/020, SC-001). |
| — | Engine decision made deliberately in research | ✅ PASS | research.md R1: build on Textual; custom rendering rejected with rationale. |
| — | Versioned event schema from first release | ✅ PASS | Envelope `version: "1"`, validated on ingestion; JSON Schema published in contracts/. |
| — | New runtime dependencies justified | ✅ PASS | Single runtime dep: Textual (R1). Pydantic rejected (R4); everything else is dev-only. |

**Post-Phase-1 re-check (2026-06-12)**: design artifacts (data-model.md,
contracts/, quickstart.md) introduce no new dependencies and preserve the
layer boundaries above. GATE: PASS — no Complexity Tracking entries needed.

## Project Structure

### Documentation (this feature)

```text
specs/001-core-library-foundation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   ├── event-envelope.schema.json   # Versioned event envelope (JSON Schema)
│   └── public-api.md                # Public API surface of the core library
├── checklists/
│   └── requirements.md  # Spec quality checklist (passed)
└── tasks.md             # Phase 2 output (/speckit-tasks — NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
pyproject.toml               # hatchling build, uv-managed
src/intui/
├── __init__.py              # public API re-exports
├── events/                  # ── pure Python, no Textual imports ──
│   ├── envelope.py          # Event dataclass, scope, validation, versioning
│   ├── stream.py            # EventStream, append-only + dedupe, StreamHealth
│   ├── recording.py         # JSONL writer/reader, replay
│   └── sources.py           # EventSource protocol (file now, live later)
├── state/
│   ├── reducer.py           # Reducer protocol, composition, error isolation
│   ├── snapshot.py          # immutable Snapshot, state version
│   └── store.py             # Store: ingest → reduce → publish
├── viewmodels/
│   ├── selector.py          # selector/projection functions, memoization
│   └── health.py            # built-in stream-health view model
├── actions/
│   ├── intents.py           # Intent dataclass, risky flag, handler protocol
│   └── confirm.py           # confirmation flow state machine
├── theming/
│   ├── theme.py             # Theme tokens (palette/emphasis/status)
│   └── default.py           # default dark theme
├── widgets/                 # ── Textual layer ──
│   ├── bridge.py            # store ⇄ Textual reactivity, render coalescing
│   ├── bound.py             # view-model-bound widget base
│   └── signal.py            # Signal primitive (color+motion+text counterpart)
└── app.py                   # IntuiApp shell wiring pipeline, theme, intents

tests/
├── unit/                    # envelope, stream, reducers, store, selectors,
│                            #   intents, themes (headless, no Textual)
├── replay/                  # recorded JSONL fixtures + determinism tests
└── snapshot/                # Pilot-driven app tests + visual snapshots

examples/
└── hello_replay/
    ├── README.md            # documented fresh-checkout run steps
    ├── app.py               # the example application
    └── recording.jsonl      # bundled sample event stream

docs/                        # existing reference docs (unchanged)
```

**Structure Decision**: Single library project with `src/` layout. The layer
boundary inside the package is enforced by import direction:
`events/state/viewmodels/actions/theming` are pure Python (lint rule: no
`textual` imports); `widgets/` and `app.py` are the only Textual-facing
modules. Examples live at the repo root as first-class deliverables
(Principle VIII), depending only on `intui`'s public API.

## Complexity Tracking

No constitutional violations — table intentionally empty.
