# Tasks: Operator Console

**Input**: Design documents from `/specs/005-operator-console/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/console-api.md

**Tests**: Per Constitution Principle VII, tests for `intui.kit.state.modes` and `intui.kit.state.conversation` (reductions, selectors, switch_mode_intent) are REQUIRED and written first. Component + example behavior uses Pilot tests.

**Organization**: US1 (modes) and US2 (conversation) add the reusable pieces; US3 is the flagship `operator_console` example composing the whole kit.

## Format: `[ID] [P?] [Story] Description`

## Phase 1: Setup

- [ ] T001 Add ruff per-file-ignores for `src/intui/kit/mode_strip.py` and `src/intui/kit/conversation_log.py` in `pyproject.toml` (kit.state stays banned; the layering guard already covers `intui.kit.state`)

## Phase 2: Foundational (mode + conversation models — blocks the stories)

- [ ] T002 [P] Failing tests for the mode model in `tests/unit/test_modes.py`: `mode_slice` seeds modes + initial current, `mode_changed` switches current, unknown mode ignored, `mode_view` entries with active flag, `switch_mode_intent` builds Intent("switch_mode", {"mode": ...}); memoization
- [ ] T003 [P] Failing tests for the conversation model in `tests/unit/test_conversation.py`: `message_added`/`question_requested`/`approval_requested` reduce into ordered entries with role/kind, unknown role tolerated, `conversation_view` rows + tags, memoization
- [ ] T004 Implement `src/intui/kit/state/modes.py` (ModeState, mode_slice, mode_view, ModeEntry/ModeView, switch_mode_intent)
- [ ] T005 Implement `src/intui/kit/state/conversation.py` (ConversationEntry/State, conversation_slice, conversation_view, ConversationKind/Row/View)
- [ ] T006 Export both models from `src/intui/kit/state/__init__.py` and add the components to the lazy exports in `src/intui/kit/__init__.py`

**Checkpoint**: mode + conversation models complete and headlessly tested.

## Phase 3: User Story 1 — Modes (P1) [MVP]

- [ ] T007 [US1] Pilot tests (write first) in `tests/snapshot/test_mode_strip.py`: renders all modes with active marked (non-color), pressing a mode key posts a `switch_mode` intent, `mode_changed` re-highlights, switching to the active mode is a no-op
- [ ] T008 [US1] Implement `ModeStrip` in `src/intui/kit/mode_strip.py` (BoundContainer over `mode_view`; registers `keys` via `IntuiApp.bind_key` to post `switch_mode_intent`)

**Checkpoint**: mode strip switches modes through the intent→event loop.

## Phase 4: User Story 2 — Conversation surface (P2)

- [ ] T009 [US2] Pilot tests (write first) in `tests/snapshot/test_conversation_log.py`: transcript in arrival order, role/kind tags identifiable without color, question vs message distinct, auto-scroll to latest, empty state
- [ ] T010 [US2] Implement `ConversationLog` in `src/intui/kit/conversation_log.py` (BoundContainer over `conversation_view`; scrollable, auto-scroll to end)

**Checkpoint**: conversation transcript renders all entry kinds.

## Phase 5: User Story 3 — The operator console example (P1)

- [ ] T011 [US3] Create committed `examples/operator_console/recording.jsonl` (one narrative: messages + question + approval, `mode_changed`s, task/work-item/lane vocabulary, a `diff_ready`, an `evidence_ready`)
- [ ] T012 [US3] Implement `examples/operator_console/app.py` + `__main__.py`: store with modes/conversation/taskboard/artifacts slices; persistent mode strip + conversation + signal; per-mode content switch (Plan/Build/Inspect/Review) composing chip/tree/lanes/diff/evidence; `switch_mode` handler appends `mode_changed`; command bar + palette
- [ ] T013 [US3] Pilot test in `tests/snapshot/test_operator_console.py`: launch headless, advance replay, switch through all four modes, assert each renders without error and the run completes; keyboard-only mode switching works

**Checkpoint**: the flagship console runs end to end across all modes.

## Phase 6: Polish & Cross-Cutting

- [ ] T014 [P] Extend the contract-drift test in `tests/unit/test_public_api.py` with the console-api.md names (`intui.kit.state` + `intui.kit`)
- [ ] T015 [P] Accessibility additions in `tests/snapshot/test_accessibility.py`: mode switching keyboard-only (SC-004); active mode + conversation roles color-free identifiable (SC-002)
- [ ] T016 [P] `examples/operator_console/README.md` (modes, keys, public-safe note) + root README (operator console as the flagship)
- [ ] T017 Full gate: `uv run pytest && uv run ruff check && uv run mypy`; fix all findings; fresh-clone quickstart check

## Dependencies & Execution Order

```text
Setup -> Foundational (T002-T006) -> US1 (modes) -> US2 (conversation) -> US3 (console) -> Polish
```

- US3 depends on US1 + US2 (it composes them) and on the 002/004 kit components.
- Within every phase: test tasks strictly before implementation (Principle VII).

## Implementation Strategy

MVP = Phases 1–3 (modes switchable). Then conversation, then the flagship
console assembling everything, then polish.
