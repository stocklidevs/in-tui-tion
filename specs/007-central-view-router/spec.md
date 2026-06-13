# Feature Specification: Central View Router

**Feature Branch**: `007-central-view-router`

**Created**: 2026-06-13

**Status**: Draft

**Input**: User description: "Central view router: a selectable central-pane view state with a select_view intent and a ViewRouter component, so commands and clicks route the central space to a specific view (tasks, diff, evidence, lanes), complementing the workflow modes which preselect a default view"

## Overview

A way to point the central space at a specific view on demand (R7's intent that
*Tasks / Diff / Files / Evidence* menu actions surface their view). Today the
central pane swaps only at the coarse grain of the four workflow modes
(Plan/Build/Inspect/Review). This adds a finer **view router**: a selectable
central-view state, a `select_view` intent, and a `ViewRouter` component that
shows the registered view matching the current selection. Commands and clicks
(e.g. a "Diff" command) route the center to that view.

The router **complements** modes rather than replacing them: modes remain the
high-level workflow phase and each mode *preselects a sensible default view*;
within (or across) a mode the operator can jump straight to any view. The
router is generic — a "view" is any named central panel; the application
registers which views exist and what each renders.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Route the central space to a chosen view (Priority: P1)

An operator selects a view (by command, key, or click) and the central space
shows that view; selecting another view swaps the center to it. The currently
selected view is part of derived state, and selection routes as a `select_view`
intent.

**Why this priority**: This is the core capability — a selectable central view
is the smallest complete unit and what every routing interaction builds on.

**Independent Test**: Register several views, select each by intent, and verify
the central router shows the matching view and the selected-view derived state
updates.

**Acceptance Scenarios**:

1. **Given** an application that registers named views, **When** a `view_selected`
   event for a view arrives, **Then** the selected view in derived state becomes
   that view and the router shows it.
2. **Given** the router, **When** the operator triggers `select_view` for a view
   (command/key/click), **Then** a `select_view` intent is delivered and the
   center routes to that view.
3. **Given** a `select_view`/`view_selected` for an unregistered view, **When**
   reduced, **Then** the selected view is unchanged (tolerated, no crash).
4. **Given** the selected view changes, **When** the router updates, **Then**
   only the central pane changes; surrounding surfaces are undisturbed.

---

### User Story 2 - Commands and clicks route the center (Priority: P2)

The bottom command menu's view actions (e.g. Tasks, Diff, Evidence, Lanes)
route the central space: invoking one selects the corresponding view. This works
by keyboard (the command's key) and by clicking the command, and reuses the
existing command/intent machinery.

**Why this priority**: This is the operator-facing payoff — clicking "Diff"
shows the diff. It depends on US1's router but is independently testable.

**Independent Test**: Invoke a view command from the bar/palette and verify the
center routes to that view.

**Acceptance Scenarios**:

1. **Given** a command whose intent is `select_view` for a view, **When** it is
   invoked from the menu (key or click), **Then** the center routes to that view.
2. **Given** the same command in the palette, **When** selected, **Then** the
   center routes identically.
3. **Given** a view command for the already-selected view, **When** invoked,
   **Then** it is a no-op (no flicker).

---

### User Story 3 - Modes preselect a default view (Priority: P2)

Switching workflow mode preselects that mode's default central view (e.g. Build
→ tasks, Inspect → diff, Review → evidence), so a mode change lands on a useful
view; the operator can then route to any other view without leaving the mode.

**Why this priority**: This is the "complements modes" relationship — modes give
context and a sensible starting view; the router gives precise control. It
depends on both the router (US1) and modes (feature 005).

**Independent Test**: Switch modes and verify the central view becomes that
mode's default; then select another view and verify it overrides without
changing the mode.

**Acceptance Scenarios**:

1. **Given** a mode with a configured default view, **When** the mode becomes
   active, **Then** the central view becomes that default.
2. **Given** a mode is active, **When** the operator selects a different view,
   **Then** the center shows it and the mode does not change.
3. **Given** a mode with no configured default, **When** it becomes active,
   **Then** the central view is left unchanged (no crash, no blank).

---

### Edge Cases

- Selecting a view before the router has registered any: tolerated; the router
  shows an explicit empty/placeholder state until a valid view is selected.
- A registered view id that has no corresponding pane in the router: the router
  shows the placeholder rather than crashing.
- Rapid view switching: each selection is one intent; the center stays
  responsive and lands on the last selection.
- Selecting a view while a modal (confirm/palette) is open: the modal keeps
  focus; the selection applies underneath.
- A mode default pointing at a view the router does not have: ignored gracefully.

## Requirements *(mandatory)*

### Functional Requirements

**View router model (shared)**

- **FR-001**: The system MUST define a view-router model with an ordered set of
  registered view ids and a current selected view, reduced from `view_selected`
  events, tolerating unknown view ids without changing the selection.
- **FR-002**: The system MUST expose a `select_view` intent (carrying the target
  view id) and a view-router view model (registered views + which is selected).
- **FR-003**: Selecting an unregistered view MUST be a no-op in the reduced
  state (FR/edge tolerance).

**ViewRouter component**

- **FR-004**: A `ViewRouter` component MUST render the central pane matching the
  current selected view, swapping only the central pane when the selection
  changes, and MUST show an explicit placeholder when no valid view is selected.
- **FR-005**: The application MUST be able to register named views (id → pane)
  with the router; the router MUST tolerate a selected id with no registered
  pane by showing the placeholder.
- **FR-006**: The router MUST re-render only when the selected view changes and
  stay responsive under streaming updates.

**Command + mode integration**

- **FR-007**: View selection MUST be expressible as a command (intent
  `select_view`) so the command menu/palette can route the center by key or
  click (Principle III; reuses feature 003).
- **FR-008**: The system MUST provide a way to associate each mode with a
  default view so that activating a mode preselects that view, without coupling
  the router to the mode model (a mapping the application supplies).
- **FR-009**: Selecting a view MUST NOT change the active mode; switching mode
  MUST preselect its default view (when configured) but leave manual view
  selection thereafter in effect until changed.

**Operator console integration**

- **FR-010**: The `operator_console` example MUST drive its central space
  through the `ViewRouter` with registered views (e.g. tasks, lanes, diff,
  evidence), route them via view commands in the bottom menu, and preselect a
  default view per mode.
- **FR-011**: The example MUST remain fully keyboard-operable (select views by
  key, mode switch preselects) with public-safe rendering, and run from a fresh
  checkout (Principle VIII).

**Cross-cutting**

- **FR-012**: New model logic (view reduction, selectors, mode-default mapping)
  MUST be engine-free and headlessly testable (Principle VII).
- **FR-013**: Every routed view MUST be reachable and identifiable by keyboard
  with visible focus; no routing affordance may depend on color alone.

### Key Entities

- **ViewState**: ordered registered view ids + current selected view; reduced
  from `view_selected`.
- **ViewRouterView**: ordered view entries each with id/label + selected flag.
- **select_view intent**: `select_view` carrying the target view id.
- **ViewRouter**: the central component that shows the pane for the selected
  view, with a placeholder fallback.
- **mode→default-view mapping**: an application-supplied association used to
  preselect a view when a mode activates.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Selecting any registered view routes the central pane to it every
  time (verified headlessly via the router model + component).
- **SC-002**: Invoking a view command (key, click, or palette) routes the center
  to that view (verified for all three paths).
- **SC-003**: Switching to a mode with a configured default view preselects that
  view; selecting another view afterward does not change the mode (verified).
- **SC-004**: An unregistered/placeholder view never crashes or blanks — the
  router shows an explicit placeholder.
- **SC-005**: 100% of view routing is keyboard-operable with visible focus.
- **SC-006**: The example routes tasks/lanes/diff/evidence through the central
  router over a replayed run and from a fresh checkout.

## Assumptions

- A "view" is one focused central panel; composing several widgets into a single
  view (e.g. a "tasks" view = chip + tree) is the application's choice when it
  registers the view.
- Modes (feature 005) stay as the high-level workflow phase; the router is the
  finer central-pane selector. The mode→default-view mapping lives in the
  application, not the library, to keep the router and mode models decoupled.
- View selection emits `select_view`; the application appends the
  `view_selected` event (intent → event → state), matching the mode pattern.
- Files browser, compare, and graph views (R10/R11) are out of scope as views
  here; the router is agnostic and can host them later.
- The example may reuse `operator_console`; no new gallery entry is required.
