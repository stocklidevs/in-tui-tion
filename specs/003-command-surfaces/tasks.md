# Tasks: Command Surfaces

**Input**: Design documents from `/specs/003-command-surfaces/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/commands-api.md

**Tests**: Per Constitution Principle VII, tests for `intui.kit.state.commands` (registry, availability, matcher) are REQUIRED and written first. Surface behavior uses Pilot tests.

**Organization**: US1 (bottom menu), US2 (palette) share the Phase-2 command model; `mission_control` gains both surfaces.

## Format: `[ID] [P?] [Story] Description`

## Phase 1: Setup

- [X] T001 Add ruff per-file-ignores for `src/intui/kit/command_bar.py` and `src/intui/kit/command_palette.py` in `pyproject.toml` (kit.state stays banned; the layering guard already covers `intui.kit.state`)

## Phase 2: Foundational (command model — blocks both stories)

- [X] T002 [P] Failing tests for registry + availability in `tests/unit/test_commands.py`: duplicate-id rejection, ordered `commands`, `get`, `is_available` over a snapshot, `risky` mirrors `intent.risky`
- [X] T003 [P] Failing tests for the matcher in `tests/unit/test_commands.py`: `match_score` case-insensitive subsequence (None on no match, higher for contiguous/word-boundary), `filter_commands` ranks + falls back to registry order on empty query
- [X] T004 [P] Failing tests for `command_view` selector in `tests/unit/test_commands.py`: entries mirror registry with per-snapshot `enabled`, memoization/value-equality
- [X] T005 Implement `src/intui/kit/state/commands.py`: `Command`, `CommandRegistry`, `CommandEntry`/`CommandView`, `command_view`, `match_score`, `filter_commands`
- [X] T006 Export the command model from `src/intui/kit/state/__init__.py` and add the command surfaces to the lazy exports in `src/intui/kit/__init__.py`

**Checkpoint**: command model complete and headlessly tested.

## Phase 3: User Story 1 — Bottom command menu (P1) [MVP]

- [X] T007 [US1] Pilot tests (write first) in `tests/snapshot/test_command_bar.py`: renders key+label row from registry, key press delivers intent, click delivers intent, disabled command renders marked and does not fire, availability change updates only affected entries, risky command routes through confirm, overflow shows a "more" affordance
- [X] T008 [US1] Implement `CommandBar` in `src/intui/kit/command_bar.py` (BoundContainer over `command_view`; key bindings; invoke via `post_intent`; fire-time availability re-check; resize-driven overflow)
- [X] T009 [US1] Add a `CommandBar` to `examples/mission_control/app.py` with a few commands incl. one risky; verify `uv run python -m examples.mission_control`

**Checkpoint**: menu invokes intents, respects availability + risky confirm.

## Phase 4: User Story 2 — Command palette (P2)

- [ ] T010 [US2] Pilot tests (write first) in `tests/snapshot/test_command_palette.py`: opens listing all commands, typing filters+ranks, keyboard select+confirm invokes (intent delivered), escape dismisses without invoking, disabled command not invocable, risky confirm applies, empty-state on no match
- [ ] T011 [US2] Implement `CommandPalette` modal in `src/intui/kit/command_palette.py` (query input + result list over the same registry; fire-time availability re-check; invoke via `post_intent`) and `IntuiApp.open_command_palette` in `src/intui/app.py`
- [ ] T012 [US2] Wire a palette opener into `examples/mission_control/app.py` (key + the bar's overflow "more") sharing the US1 registry

**Checkpoint**: both surfaces drive the one registry identically.

## Phase 5: Polish & Cross-Cutting

- [ ] T013 [P] Extend the contract-drift test in `tests/unit/test_public_api.py` with the commands-api.md names (`intui.kit.state` + `intui.kit`)
- [ ] T014 [P] Accessibility additions in `tests/snapshot/test_accessibility.py`: command surfaces keyboard-only (SC-002), disabled/selected states non-color (SC-006), risky confirm from both surfaces (SC-003)
- [ ] T015 [P] Update `examples/mission_control/README.md` (command menu + palette keys) and the root README kit list
- [ ] T016 Full gate: `uv run pytest && uv run ruff check && uv run mypy`; fix all findings; fresh-clone quickstart check

## Dependencies & Execution Order

```text
Setup -> Foundational (T002-T006) -> US1 (MVP) -> US2 -> Polish
```

- US2 depends on US1 only for the shared example registry (T009); the palette
  itself (T010-T011) depends only on the Phase-2 model.
- Within every phase: test tasks strictly before implementation (Principle VII).

## Implementation Strategy

MVP = Phases 1–3 (bottom menu working in the example). Then the palette, then
polish. The example grows per story (Principle VIII).
