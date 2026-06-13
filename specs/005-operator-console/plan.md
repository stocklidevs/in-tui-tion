# Implementation Plan: Operator Console

**Branch**: `005-operator-console` | **Date**: 2026-06-13 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/005-operator-console/spec.md`

## Summary

The flagship example (R13, R1) plus the two reusable pieces it needs: an
engine-free **mode model** (`mode_slice`/`mode_view`/`switch_mode_intent`,
reduced from `mode_changed`) and a **conversation model**
(`conversation_slice`/`conversation_view`, reduced from message/question/
approval events), with two `BoundContainer` components (`ModeStrip`,
`ConversationLog`). The `operator_console` example composes the whole kit
across Plan/Build/Inspect/Review modes, driven by one recorded run, with mode
switching flowing intent → event → state. Decisions in [research.md](research.md);
models in [data-model.md](data-model.md).

## Technical Context

**Language/Version**: Python 3.11–3.13 (unchanged)

**Primary Dependencies**: Textual 6.x (present). **No new runtime deps.**

**Storage**: JSONL recordings (unchanged).

**Testing**: pytest headless for `kit.state.modes`/`conversation` (reductions +
selectors); Pilot for the two components; a headless example test driving all
four modes over the replay.

**Target Platform**: unchanged (Windows/macOS/Linux/WSL terminals).

**Project Type**: library + examples gallery (unchanged).

**Performance Goals**: components re-render only on view change (FR-006);
responsive under streaming; rapid mode switching stays responsive.

**Constraints**: new model logic engine-free (lint + guard, FR-012); mode
switching via intent → event (FR-011); no color-only state.

**Scale/Scope**: mode model + conversation model + 2 components + the flagship
example. Comparison/graph/session-browser views are out of scope.

## Constitution Check

| # | Principle | Status | Notes |
|---|-----------|--------|-------|
| I | Structured State | ✅ PASS | `mode_view`/`conversation_view` are selectors over the snapshot; modes + conversation reduced from events. |
| II | Layered Architecture | ✅ PASS | New models join engine-free `kit.state`; components are layer-2; the example uses only public APIs. |
| III | Actions Are Intents | ✅ PASS | `switch_mode` intent → `mode_changed` event → state; no UI-only mode mutation in the reduced path. |
| IV | Keyboard-First, Accessible | ✅ PASS | Mode keys app-global (003 mechanism); active mode + conversation roles marked non-color (SC-004). |
| V | Meaningful Motion | ✅ PASS | The activity Signal (001) is reused in Build mode; no new decorative motion. |
| VI | Public-Safe | ✅ PASS | Inspect/Review reuse 004's default-on redaction (SC-005). |
| VII | Test-First, Replayable | ✅ PASS | Mode/conversation reductions + selectors headless test-first; components + example via Pilot. |
| VIII | Example-Driven | ✅ PASS | The deliverable *is* the flagship example over one recorded run (FR-007/008/010). |
| — | New deps justified | ✅ PASS | None. |

**Post-Phase-1 re-check (2026-06-13)**: artifacts add no dependencies and hold
the layer boundary. GATE: PASS — Complexity Tracking empty.

## Project Structure

### Documentation (this feature)

```text
specs/005-operator-console/
├── plan.md  research.md  data-model.md  quickstart.md
├── contracts/console-api.md
├── checklists/requirements.md
└── tasks.md (Phase 2 via /speckit-tasks)
```

### Source Code (repository root)

```text
src/intui/
├── kit/
│   ├── state/
│   │   ├── modes.py          # ── engine-free ── ModeState, mode_slice,
│   │   │                      #   mode_view, switch_mode_intent
│   │   └── conversation.py   # ── engine-free ── ConversationState,
│   │                         #   conversation_slice, conversation_view
│   ├── mode_strip.py         # ModeStrip (BoundContainer)
│   └── conversation_log.py   # ConversationLog (BoundContainer)

tests/
├── unit/
│   ├── test_modes.py             # mode reduction + view + switch_mode_intent
│   └── test_conversation.py      # conversation reduction + view
└── snapshot/
    ├── test_mode_strip.py        # render, active marker, key -> switch_mode
    ├── test_conversation_log.py  # transcript order, role/kind tags, empty
    └── test_operator_console.py  # headless: all four modes render over replay

examples/operator_console/        # app.py, __main__.py, README.md, recording.jsonl
```

**Structure Decision**: mode + conversation models in engine-free `kit.state`
(mirrors 002–004); `ModeStrip`/`ConversationLog` are `BoundContainer`s using
the 003 app-global key mechanism; the example owns per-mode layout via the
engine's content switcher (research R4).

## Complexity Tracking

No constitutional violations — table intentionally empty.
