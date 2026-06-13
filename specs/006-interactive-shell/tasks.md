# Tasks: Interactive Shell & Activity Strip

**Input**: Design documents from `/specs/006-interactive-shell/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/shell-api.md

**Tests**: Per Constitution Principle VII, tests for `intui.kit.state.activity` (mapping) and the `prompt_message_event` helper are REQUIRED and written first. Widget + example behavior uses Pilot tests.

**Organization**: US1 (prompt) and US2 (activity strip) are independent reusable pieces; US3 wires both into the operator console.

## Format: `[ID] [P?] [Story] Description`

## Phase 1: Setup

- [ ] T001 Add ruff per-file-ignores for `src/intui/kit/prompt_input.py` and `src/intui/kit/activity_strip.py` in `pyproject.toml` (kit.state stays banned; the layering guard already covers `intui.kit.state`)

## Phase 2: Foundational (engine-free mapping + helper)

- [ ] T002 [P] Failing tests for the activity mapping in `tests/unit/test_activity.py`: every R6 state in `ACTIVITY_STYLES` has a distinct glyph+label, motion per state (thinking/verifying swoosh, waiting/history pulse, failure strobe, passed/idle steady), `activity_style` fallback for unknown state keeps raw label
- [ ] T003 [P] Failing tests for `prompt_message_event` in `tests/unit/test_conversation.py`: builds a `message_added` role=user event with the text; reduces into a user conversation entry
- [ ] T004 Implement `src/intui/kit/state/activity.py` (ACTIVITY_STATES, ACTIVITY_STYLES, activity_style)
- [ ] T005 Implement `prompt_message_event` in `src/intui/kit/state/conversation.py`
- [ ] T006 Export both from `src/intui/kit/state/__init__.py` and add the widgets to the lazy exports in `src/intui/kit/__init__.py`

**Checkpoint**: activity mapping + event helper complete and headlessly tested.

## Phase 3: User Story 1 — Prompt surface (P1) [MVP]

- [ ] T007 [US1] Pilot tests (write first) in `tests/snapshot/test_prompt_input.py`: typing + Enter posts `prompt_submitted` with the text and clears, empty/whitespace submits nothing, prompt is keyboard-focusable
- [ ] T008 [US1] Implement `PromptInput` in `src/intui/kit/prompt_input.py` (wraps engine Input; on submit posts the intent via `post_intent`, clears; no-empty guard)

**Checkpoint**: typing a prompt delivers an intent and clears.

## Phase 4: User Story 2 — Activity strip (P1)

- [ ] T009 [US2] Pilot tests (write first) in `tests/snapshot/test_activity_strip.py`: each state renders its color/motion + textual label (identifiable without color), unknown state neutral fallback, width-responsive track keeps the label on resize
- [ ] T010 [US2] Implement `ActivityStrip` in `src/intui/kit/activity_strip.py` (Signal subclass with `ACTIVITY_STYLES`; track length follows widget width on mount/resize, min track keeps label)

**Checkpoint**: the KITT strip reflects every activity state prominently.

## Phase 5: User Story 3 — Wire into the operator console (P1)

- [ ] T011 [US3] Add `ActivityStrip` (docked top, above the mode strip) bound to the run-status selector, extending `run_status_reducer` to emit R6 states (thinking/verifying/passed/failure/idle); add `PromptInput` docked at the bottom (above the command bar)
- [ ] T012 [US3] Implement the submit→reply loop in `operator_console` `handle_intent`: on `prompt_submitted`, append the user message (`prompt_message_event`), set a transient `thinking` activity state, schedule a scripted agent `message_added` reply, then restore run state
- [ ] T013 [US3] Pilot test in `tests/snapshot/test_operator_console.py` (extend): submit a prompt → appears as a user entry, an agent reply follows, the activity strip reflects state; keyboard-only submission works

**Checkpoint**: the console is operable — type a prompt, watch the strip, read the reply.

## Phase 6: Polish & Cross-Cutting

- [ ] T014 [P] Extend the contract-drift test in `tests/unit/test_public_api.py` with the shell-api.md names (`intui.kit.state` + `intui.kit`)
- [ ] T015 [P] Accessibility additions in `tests/snapshot/test_accessibility.py`: prompt submission keyboard-only (SC-004); activity states color-free identifiable (SC-003)
- [ ] T016 [P] Update `examples/operator_console/README.md` (prompt + activity strip, keys) and the root README
- [ ] T017 Full gate: `uv run pytest && uv run ruff check && uv run mypy`; fix all findings; fresh-clone quickstart check

## Dependencies & Execution Order

```text
Setup -> Foundational (T002-T006) -> US1 (prompt) + US2 (strip) -> US3 (console) -> Polish
```

- US1 and US2 are independent; US3 composes both. Within every phase: test
  tasks strictly before implementation (Principle VII).

## Implementation Strategy

MVP = Phases 1–3 (prompt submits). Then the activity strip, then the console
wiring (the visible payoff), then polish.
