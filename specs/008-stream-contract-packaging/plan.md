# Implementation Plan: Stream Contract & Packaging

**Branch**: `008-stream-contract-packaging` | **Date**: 2026-06-13 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/008-stream-contract-packaging/spec.md`

## Summary

The adoption on-ramp: consolidate the event vocabulary into a canonical,
documented **stream contract** with per-reducer type constants unioned into
`KNOWN_EVENT_TYPES`, an engine-free **validator** (`validate_event`/
`validate_stream`), a published envelope **JSON Schema**, **pip-installable
packaging** (dynamic single-source version, full metadata, `py.typed`, verified
clean install), and an **author quickstart**. No new UI components; this is what
the upcoming zero-config runner and IntentForge adapter will target. Decisions
in [research.md](research.md); shapes in [data-model.md](data-model.md).

## Technical Context

**Language/Version**: Python 3.11–3.13 (unchanged)

**Primary Dependencies**: Textual 6.x (runtime, unchanged). **No new runtime
deps** — the validator is hand-rolled. Dev-only: `jsonschema` (to verify the
published schema language-agnostically).

**Storage**: JSONL (unchanged).

**Testing**: pytest headless for the validator, the vocabulary registry + drift
guard, the JSON Schema check, and the version single-source; a scripted
build+clean-install check for the wheel.

**Target Platform**: unchanged (Windows/macOS/Linux/WSL).

**Project Type**: library + examples gallery (unchanged).

**Performance Goals**: validation is streaming/line-by-line (no whole-file load).

**Constraints**: validator + registry engine-free (lint + guard, FR-012);
single version source (FR-008); contract is the single vocabulary source
(FR-011).

**Scale/Scope**: contract doc + schema + validator + registry + packaging +
quickstart. PyPI upload, per-type payload schemas, the runner, and the IF
adapter are out of scope.

## Constitution Check

| # | Principle | Status | Notes |
|---|-----------|--------|-------|
| I | Structured State | ✅ PASS (n/a) | No new state; formalizes the event contract the pipeline already uses. |
| II | Layered Architecture | ✅ PASS | Validator in foundation (vocabulary injected); registry in kit; no inverted deps. |
| III | Actions Are Intents | ✅ PASS (n/a) | No new actions. |
| IV | Keyboard-First, Accessible | ✅ PASS (n/a) | No UI. |
| V | Meaningful Motion | ✅ PASS (n/a) | — |
| VI | Public-Safe | ✅ PASS | Contract documents the public-safety flag + default-on redaction guidance (FR-013). |
| VII | Test-First, Replayable | ✅ PASS | Validator + registry + version + schema all headless test-first. |
| VIII | Example-Driven | ✅ PASS | Quickstart + contract make the existing examples reachable; no example regresses. |
| — | New deps justified | ✅ PASS | Only dev-only `jsonschema` for the schema check; no runtime deps. |

**Post-Phase-1 re-check (2026-06-13)**: only a dev-dependency added; layering
holds. GATE: PASS — Complexity Tracking empty.

## Project Structure

### Documentation (this feature)

```text
specs/008-stream-contract-packaging/
├── plan.md  research.md  data-model.md  quickstart.md
├── contracts/contract-api.md
├── checklists/requirements.md
└── tasks.md (Phase 2 via /speckit-tasks)
```

### Source / repo changes

```text
src/intui/
├── __init__.py            # __version__ = single source (bump to 0.8.0)
├── py.typed               # NEW — PEP 561 marker
├── events/
│   ├── validate.py        # NEW — StreamIssue, validate_event, validate_stream
│   └── __init__.py        # export the validator
└── kit/state/
    ├── reduce.py          # + TASKBOARD_EVENT_TYPES (reducer uses it)
    ├── artifacts.py       # + ARTIFACT_EVENT_TYPES
    ├── conversation.py    # + CONVERSATION_EVENT_TYPES
    ├── modes.py           # + MODE_EVENT_TYPES
    ├── views.py           # + VIEW_EVENT_TYPES
    └── __init__.py        # + KNOWN_EVENT_TYPES (union) + re-exports

pyproject.toml             # dynamic version, metadata, classifiers, urls, jsonschema dev dep
LICENSE                    # NEW — MIT text (metadata references it)

docs/
├── event-stream-contract.md            # NEW — canonical vocabulary + conventions
├── quickstart.md                       # NEW — stream-first + build-in-code
└── contracts/event-envelope.schema.json  # NEW — published schema

tests/
├── unit/
│   ├── test_validate.py        # validator errors/warnings, line numbers, record-wrapping
│   ├── test_vocabulary.py      # registry = union; drift guard (declared types really handled)
│   └── test_version.py         # __version__ == importlib.metadata version; single source
└── unit/test_schema.py         # published JSON Schema validates envelopes (jsonschema, dev)

scripts or test: a build + clean-install check (wheel contains py.typed; import works)
```

**Structure Decision**: validator in engine-free `intui.events`; vocabulary
constants live with each reducer and union in `intui.kit.state` (cannot drift —
the reducer uses the constant); published schema + docs at repo `docs/`;
packaging via hatchling dynamic version + `py.typed`.

## Complexity Tracking

No constitutional violations — table intentionally empty.
