# Tasks: Core Library Foundation

**Input**: Design documents from `/specs/001-core-library-foundation/`

**Prerequisites**: plan.md (required), spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Per Constitution Principle VII, tests for core logic (events, state, view models, actions, theming) are REQUIRED and written first (failing before implementation). Widget/visual behavior uses Textual Pilot and snapshot tests.

**Organization**: Tasks are grouped by user story from spec.md. The runnable example grows incrementally — each story phase extends it, keeping every phase independently demonstrable (Principle VIII).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: US1 (pipeline+rendering), US2 (replay/headless), US3 (intents), US4 (theming/signals)

## Phase 1: Setup

**Purpose**: Project skeleton, tooling, and the layer-boundary guard.

- [X] T001 Create `pyproject.toml` (hatchling backend, `intui` package in src layout, runtime dep `textual>=6,<7`, dev deps pytest/pytest-asyncio/pytest-textual-snapshot/ruff/mypy) and verify `uv sync` succeeds
- [X] T002 Create package skeleton per plan.md: `src/intui/__init__.py` and empty modules under `src/intui/{events,state,viewmodels,actions,theming,widgets}/` plus `src/intui/app.py`, and test dirs `tests/{unit,replay,snapshot}/`
- [X] T003 [P] Configure ruff and mypy in `pyproject.toml` (mypy strict for `intui.events/state/viewmodels/actions/theming`; standard for widgets/app)
- [X] T004 [P] Add layering guard test in `tests/unit/test_layering.py` asserting no `textual` import (direct or transitive) in `intui.events/state/viewmodels/actions/theming` — this test stays green for the life of the project

**Checkpoint**: `uv sync`, `uv run pytest`, `uv run ruff check`, `uv run mypy` all run (guard test passes against empty modules).

## Phase 2: Foundational (blocking prerequisites)

**Purpose**: The versioned event model every story consumes. Tests first.

- [X] T005 [P] Write failing tests for envelope validation in `tests/unit/test_envelope.py`: parse_event happy path, each required-field failure, unknown envelope version rejected, unknown event *type* accepted, frozen immutability, `public_safe` payload metadata preserved (contract: `contracts/event-envelope.schema.json`)
- [X] T006 Implement `Event`, `Scope`, `EnvelopeError`, `parse_event` in `src/intui/events/envelope.py`
- [X] T007 [P] Write failing tests for stream semantics in `tests/unit/test_stream.py`: append-only, duplicate `event_id` dropped and counted, `StreamHealth` transitions (live/ended/disconnected/erroring per data-model.md)
- [X] T008 Implement `EventStream`, `StreamState`, `StreamHealth` in `src/intui/events/stream.py`
- [X] T009 Write failing tests then implement `EventSource` protocol and `MemorySource` in `src/intui/events/sources.py` (tests in `tests/unit/test_sources.py`)

**Checkpoint**: Event model complete and headlessly tested — user story phases can begin.

## Phase 3: User Story 1 — Build a TUI from structured state (Priority: P1) [MVP]

**Goal**: events → reducers → immutable snapshots → memoized view models → auto-rendering widgets; no imperative repaints.

**Independent Test**: feed a scripted event sequence through a small app; rendered output reflects each state change with no screen-drawing code in the app (spec US1).

### Tests for User Story 1 (write first, ensure they FAIL)

- [X] T010 [P] [US1] Failing tests for snapshot/reducer in `tests/unit/test_state.py`: structural snapshot equality, monotonic `state_version`, `compose_reducers` slice ownership, unknown event type passes through unchanged, deterministic reduction (same sequence => equal snapshots)
- [X] T011 [P] [US1] Failing tests for store in `tests/unit/test_store.py`: ingest→reduce→publish, dedupe via stream, subscriber notification, reducer exception isolated (`ReducerError` in health, prior snapshot retained)
- [X] T012 [P] [US1] Failing tests for selectors in `tests/unit/test_selectors.py`: memoization per state_version, value-equality of view models, built-in `health_view`

### Implementation for User Story 1

- [X] T013 [P] [US1] Implement `Snapshot` and `ReducerError` in `src/intui/state/snapshot.py` and `Reducer` protocol + `compose_reducers` in `src/intui/state/reducer.py`
- [X] T014 [US1] Implement `Store` (ingest, subscribe, snapshot property) in `src/intui/state/store.py` (depends on T013)
- [X] T015 [P] [US1] Implement `selector` memoization in `src/intui/viewmodels/selector.py` and `health_view` in `src/intui/viewmodels/health.py`
- [X] T016 [US1] Implement store-to-Textual bridge with render coalescing in `src/intui/widgets/bridge.py` and `BoundWidget` (re-render only on view-model change) in `src/intui/widgets/bound.py`
- [X] T017 [US1] Implement minimal `IntuiApp` shell (store + source wiring, ingestion as async task, minimal `Theme`/`DEFAULT_THEME` token stubs in `src/intui/theming/theme.py` + `default.py`) in `src/intui/app.py`
- [X] T018 [US1] Pilot-driven app tests in `tests/snapshot/test_us1_pipeline.py`: initial state renders, new event updates only the bound widget, unknown event type doesn't blank/crash (spec US1 acceptance scenarios)
- [X] T019 [US1] Create example skeleton `examples/hello_replay/app.py` + `examples/hello_replay/__main__.py` rendering a scrolling item list and status line from a `MemorySource` scripted sequence; runnable via `uv run python -m examples.hello_replay`

**Checkpoint**: MVP — a state-driven TUI renders and updates from events, fully testable.

## Phase 4: User Story 2 — Replay a recorded session, test headlessly (Priority: P2)

**Goal**: lossless JSONL recording/replay; deterministic, terminal-free verification.

**Independent Test**: record a stream, replay it headless and rendered; final snapshots identical across runs (spec US2).

### Tests for User Story 2 (write first, ensure they FAIL)

- [X] T020 [P] [US2] Failing tests for recording round-trip in `tests/unit/test_recording.py`: write→read lossless, malformed line reported with line number + reason, `skip` vs `halt` modes, older-supported-version envelope accepted
- [X] T021 [P] [US2] Failing determinism suite in `tests/replay/test_determinism.py` with committed fixture `tests/replay/fixtures/sample_run.jsonl`: replay twice => identical final snapshots; headless replay equals live-run snapshot

### Implementation for User Story 2

- [X] T022 [US2] Implement `write_recording`/`read_recording` (JSONL, UTF-8) in `src/intui/events/recording.py`
- [X] T023 [US2] Implement `JsonlReplaySource` (optional `rate` pacing, `on_malformed` policy) in `src/intui/events/sources.py`
- [X] T024 [US2] Implement `Store.run(source)` async drive: per-event failures never raise, returns terminal `StreamHealth`; tests in `tests/unit/test_store_run.py` (ended/disconnected/erroring outcomes)
- [X] T025 [US2] Switch the example to replay a bundled `examples/hello_replay/recording.jsonl` (create the recording: a simulated multi-step run with statuses for later signal states) and show stream health when the recording ends

**Checkpoint**: recordings are the test backbone; example replays a real file.

## Phase 5: User Story 3 — React to user input through intents (Priority: P2)

**Goal**: keyboard-first input delivered as named intents; risky intents confirmed before delivery.

**Independent Test**: simulate key presses; app handler receives named intents; risky intent requires confirmation; keyboard-only operation (spec US3).

### Tests for User Story 3 (write first, ensure they FAIL)

- [ ] T026 [P] [US3] Failing tests for intents in `tests/unit/test_intents.py`: `Intent` immutability/payload, handler protocol delivery, library never mutates app state (handler is sole mutation seam)
- [ ] T027 [P] [US3] Failing tests for confirmation state machine in `tests/unit/test_confirm.py`: created→confirming→confirmed delivery, cancelled never delivered, non-risky bypasses confirmation

### Implementation for User Story 3

- [ ] T028 [US3] Implement `Intent` + `IntentHandler` protocol in `src/intui/actions/intents.py`
- [ ] T029 [US3] Implement confirmation flow state machine in `src/intui/actions/confirm.py`
- [ ] T030 [US3] Wire `IntuiApp.post_intent`, keybinding registration for actions, and the built-in confirmation prompt (modal) in `src/intui/app.py`; Pilot tests in `tests/snapshot/test_us3_intents.py` (shortcut → intent delivered with payload; risky → confirm prompt → confirm/cancel paths; all actions keyboard-reachable)
- [ ] T031 [US3] Add intents to the example: `r` (re-run replay, normal) and `x` (clear history, risky/confirmable); handler appends events back through the source

**Checkpoint**: the unidirectional loop is closed — input → intent → app → events → UI.

## Phase 6: User Story 4 — Theme and signal with meaning (Priority: P3)

**Goal**: runtime-switchable token themes; the data-driven Signal primitive with non-color counterparts.

**Independent Test**: switch themes at runtime with no widget changes; drive a status field through transitions and observe color+motion+text updates (spec US4).

### Tests for User Story 4 (write first, ensure they FAIL)

- [ ] T032 [P] [US4] Failing tests for theme tokens in `tests/unit/test_theming.py`: complete default theme (palette/emphasis/status colors per data-model.md), token lookup, theme equality/naming
- [ ] T033 [P] [US4] Failing tests for signal status mapping in `tests/unit/test_signal_logic.py` (pure logic: status → StatusStyle resolution, mandatory glyph+label counterpart enforced, unknown status fallback)

### Implementation for User Story 4

- [ ] T034 [US4] Complete `Theme` tokens and `DEFAULT_THEME` (dark) in `src/intui/theming/theme.py` + `src/intui/theming/default.py`; map tokens onto Textual CSS variables and implement `IntuiApp.set_theme` runtime switch in `src/intui/app.py`
- [ ] T035 [US4] Implement `Signal` widget with `MotionMode` (steady/pulse/swoosh/strobe) and `StatusStyle` in `src/intui/widgets/signal.py` — appearance derived exclusively from bound selector
- [ ] T036 [US4] Pilot + snapshot tests in `tests/snapshot/test_us4_theming.py`: theme switch restyles without widget changes; signal transitions across working→waiting→succeeded→failed; status distinguishable with color disabled (glyph/label present)
- [ ] T037 [US4] Add to example: `t` theme-switch binding (second minimal theme inline in the example) and Signal in the header bound to the replayed run's status

**Checkpoint**: all four stories complete; example demonstrates every shipped capability.

## Phase 7: Polish & Cross-Cutting Concerns

- [ ] T038 [P] Write `examples/hello_replay/README.md` (fresh-checkout steps per quickstart.md, keybinding list incl. `?` help) and root `README.md` (project identity, layers, quickstart link)
- [ ] T039 [P] Performance/responsiveness test in `tests/replay/test_responsiveness.py`: 1,000+ event recording at 100 events/sec — UI keeps rendering and accepting input (SC-003), renders coalesce (no unbounded queue)
- [ ] T040 [P] Accessibility audit tests in `tests/snapshot/test_accessibility.py`: every primary example action keyboard-operable (SC-004); every color-coded status identifiable with color disabled (SC-006)
- [ ] T041 Public API re-exports in `src/intui/__init__.py` matching `contracts/public-api.md` exactly; contract-drift test in `tests/unit/test_public_api.py`
- [ ] T042 Full gate: `uv run pytest && uv run ruff check && uv run mypy`; fix all findings; verify quickstart steps from a clean clone (SC-001)

## Dependencies & Execution Order

- **Setup (P1) → Foundational (P2)**: blocks everything.
- **US1 (Phase 3)**: depends only on Foundational. **This is the MVP.**
- **US2 (Phase 4)**: depends on Foundational + Store (T014). Independent of US3/US4.
- **US3 (Phase 5)**: depends on the app shell (T017). Independent of US2/US4 (pure-logic tasks T026-T029 only need Setup).
- **US4 (Phase 6)**: depends on the app shell (T017) and theme stubs. Independent of US2/US3.
- **Polish (Phase 7)**: depends on all stories.
- Within every story: test tasks strictly before their implementation tasks (Principle VII).

```text
Setup -> Foundational -> US1 (MVP) -+-> US2 -+
                                    +-> US3 -+-> Polish
                                    +-> US4 -+
```

## Parallel Execution Examples

- **Setup**: T003 with T004 after T002.
- **Foundational**: T005 with T007 (test authoring); T009 after T006/T008.
- **US1**: T010, T011, T012 in parallel (tests), then T013 with T015 (different modules).
- **After US1**: US2 (T020-T025), US3 (T026-T031), and US4 (T032-T037) can proceed in parallel — they touch disjoint modules; only T030/T034 both edit `app.py` (serialize those two).
- **Polish**: T038, T039, T040 in parallel.

## Implementation Strategy

**MVP first**: Phases 1-3 deliver a working, tested, state-driven TUI (US1). Stop and demo there if needed.

**Incremental delivery**: each subsequent story lands as an independently testable increment that also extends the single example app — after every phase the example still runs and shows strictly more (Principle VIII). Suggested order: US2 next (it makes everything after it cheaper to test), then US3, then US4 — matching spec priorities.
