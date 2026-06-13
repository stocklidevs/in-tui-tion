# Implementation Plan: Interactive Shell & Activity Strip

**Branch**: `006-interactive-shell` | **Date**: 2026-06-13 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/006-interactive-shell/spec.md`

## Summary

Two additions that make the console operable: a `PromptInput` (wraps the engine
Input; Enter submits non-empty text as a `prompt_submitted` intent and clears),
plus an engine-free `prompt_message_event` helper; and an `ActivityStrip` (a
full-width preset of the Signal primitive bound to an activity-state selector,
using an engine-free `ACTIVITY_STYLES` R6 mapping, width-responsive). Both are
wired into the `operator_console` example: the strip as the headline top
element, the prompt persistent at the bottom, with a scripted reply loop.
Decisions in [research.md](research.md); model in [data-model.md](data-model.md).

## Technical Context

**Language/Version**: Python 3.11–3.13 (unchanged)

**Primary Dependencies**: Textual 6.x (present). **No new runtime deps.**

**Storage**: JSONL recordings (unchanged).

**Testing**: pytest headless for `kit.state.activity` (mapping) and the
`prompt_message_event` helper; Pilot for `PromptInput` (submit/clear/no-empty)
and `ActivityStrip` (state→render, resize); example test for the live loop.

**Target Platform**: unchanged (Windows/macOS/Linux/WSL terminals).

**Project Type**: library + examples gallery (unchanged).

**Performance Goals**: strip re-renders only on state change + animation tick;
prompt is interaction-driven; console stays responsive.

**Constraints**: activity mapping + event helper engine-free (lint + guard,
FR-014); prompt routes via intent only (FR-004, Principle III); strip state is
non-color-identifiable (FR-007).

**Scale/Scope**: PromptInput + ActivityStrip + activity mapping + event helper +
example wiring. Multi-line input, history, and slash parsing are out of scope.

## Constitution Check

| # | Principle | Status | Notes |
|---|-----------|--------|-------|
| I | Structured State | ✅ PASS | Strip binds to an activity-state selector; the prompt's submission becomes a `message_added` event via the helper. |
| II | Layered Architecture | ✅ PASS | `activity.py` + the helper join engine-free `kit.state`; `PromptInput`/`ActivityStrip` are layer-2 widgets on public APIs. |
| III | Actions Are Intents | ✅ PASS | The prompt emits `prompt_submitted` and never mutates state itself; the app appends the user message. |
| IV | Keyboard-First, Accessible | ✅ PASS | Prompt is keyboard-only operable; the strip's state is glyph+label identifiable without color (SC-003/004). |
| V | Meaningful Motion | ✅ PASS (central) | The strip is the R6 KITT signal made prominent — data-driven swoosh/strobe by state, no decorative motion. |
| VI | Public-Safe | ✅ PASS (n/a) | No new evidence surfaces; the prompt echoes operator-typed text only. |
| VII | Test-First, Replayable | ✅ PASS | Activity mapping + event helper headless test-first; widgets + example via Pilot. |
| VIII | Example-Driven | ✅ PASS | The flagship gains both as first-class elements with a live submit→reply loop (FR-010/011/012). |
| — | New deps justified | ✅ PASS | None — reuses engine Input + Signal. |

**Post-Phase-1 re-check (2026-06-13)**: artifacts add no dependencies and hold
the layer boundary. GATE: PASS — Complexity Tracking empty.

## Project Structure

### Documentation (this feature)

```text
specs/006-interactive-shell/
├── plan.md  research.md  data-model.md  quickstart.md
├── contracts/shell-api.md
├── checklists/requirements.md
└── tasks.md (Phase 2 via /speckit-tasks)
```

### Source Code (repository root)

```text
src/intui/
├── kit/
│   ├── state/
│   │   ├── activity.py        # ── engine-free ── ACTIVITY_STATES/STYLES, activity_style
│   │   └── conversation.py    # + prompt_message_event helper
│   ├── prompt_input.py        # PromptInput (wraps engine Input)
│   └── activity_strip.py      # ActivityStrip (Signal preset, full-width)

tests/
├── unit/
│   ├── test_activity.py           # ACTIVITY_STYLES mapping + fallback
│   └── test_conversation.py       # + prompt_message_event
└── snapshot/
    ├── test_prompt_input.py       # submit -> intent + clear, no empty submit, focus
    └── test_activity_strip.py     # state -> color/motion/label, resize, fallback

examples/operator_console/         # add ActivityStrip (top) + PromptInput (bottom) + reply loop
```

**Structure Decision**: activity mapping + event helper in engine-free
`kit.state`; `PromptInput` wraps the engine Input and `ActivityStrip`
subclasses Signal (research R1/R2); the example owns the scripted reply loop.

## Complexity Tracking

No constitutional violations — table intentionally empty.
