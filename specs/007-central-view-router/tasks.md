# Tasks: Central View Router

**Input**: Design documents from `/specs/007-central-view-router/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/router-api.md

**Tests**: Per Constitution Principle VII, tests for `intui.kit.state.views` (reduction, selector, select_view_intent) are REQUIRED and written first. Component + example behavior uses Pilot tests.

**Organization**: US1 (router model + component), US2 (command routing), US3 (mode-default preselect, in the example).

## Format: `[ID] [P?] [Story] Description`

## Phase 1: Setup

- [ ] T001 Add ruff per-file-ignore for `src/intui/kit/view_router.py` in `pyproject.toml` (kit.state stays banned; the layering guard already covers `intui.kit.state`)

## Phase 2: Foundational (view model)

- [ ] T002 [P] Failing tests for the view model in `tests/unit/test_views.py`: `view_slice` seeds views + initial current, `view_selected` switches current, unknown id ignored, `view_router_view` entries with selected flag (+ optional label map), `select_view_intent` builds Intent("select_view", {"view": ...}); memoization
- [ ] T003 Implement `src/intui/kit/state/views.py` (ViewState, view_slice, view_router_view, ViewEntry/ViewRouterView, select_view_intent)
- [ ] T004 Export the view model from `src/intui/kit/state/__init__.py` and add `ViewRouter` to the lazy exports in `src/intui/kit/__init__.py`

**Checkpoint**: view model complete and headlessly tested.

## Phase 3: User Story 1 — ViewRouter component (P1) [MVP]

- [ ] T005 [US1] Pilot tests (write first) in `tests/snapshot/test_view_router.py`: registers panes by id and shows the selected one, `view_selected` swaps the central pane, unknown/empty selection shows the placeholder, only the central pane changes
- [ ] T006 [US1] Implement `ViewRouter` in `src/intui/kit/view_router.py` (BoundContainer wrapping ContentSwitcher; mounts `view-{id}` panes + `view-placeholder`; binds `view_router_view` to set current)

**Checkpoint**: selecting a view routes the central pane.

## Phase 4: User Story 2 — Commands route the center (P2)

- [ ] T007 [US2] In `examples/operator_console`, add view commands to the bottom menu whose intents are `select_view_intent("tasks"|"lanes"|"diff"|"evidence")`; handle `select_view` in `handle_intent` by emitting a `view_selected` event
- [ ] T008 [US2] Pilot test (extend `tests/snapshot/test_operator_console.py`): invoking a view command (key) routes the center to that view; invoking the already-selected view is a no-op

**Checkpoint**: clicking/keying a view command routes the center.

## Phase 5: User Story 3 — Modes preselect a default view (P2)

- [ ] T009 [US3] In `examples/operator_console`, replace the mode-pane ContentSwitcher with the `ViewRouter` (views: tasks=chip+tree, lanes, diff, evidence); add a `MODE_DEFAULT_VIEW` map and, on `switch_mode`, emit both `mode_changed` and the mode's default `view_selected`
- [ ] T010 [US3] Pilot test (extend): switching mode preselects its default view; selecting another view afterward does not change the mode

**Checkpoint**: modes set a default central view; the router gives precise control.

## Phase 6: Polish & Cross-Cutting

- [ ] T011 [P] Extend the contract-drift test in `tests/unit/test_public_api.py` with the router-api.md names (`intui.kit.state` + `intui.kit`)
- [ ] T012 [P] Accessibility additions in `tests/snapshot/test_accessibility.py`: view routing keyboard-only (SC-005); placeholder/selection identifiable without color
- [ ] T013 [P] Update `examples/operator_console/README.md` (view commands + central router, mode defaults) and the root README
- [ ] T014 Full gate: `uv run pytest && uv run ruff check && uv run mypy`; fix all findings; fresh-clone quickstart check

## Dependencies & Execution Order

```text
Setup -> Foundational (T002-T004) -> US1 (router) -> US2 (commands) -> US3 (mode defaults) -> Polish
```

- US2 and US3 both build on the router (US1) and live in the example. Within
  every phase: test tasks strictly before implementation (Principle VII).

## Implementation Strategy

MVP = Phases 1–3 (router routes the center). Then command routing, then
mode-default preselect (the complement relationship), then polish.
