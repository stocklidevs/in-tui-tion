# Feature Specification: Operator Console

**Feature Branch**: `005-operator-console`

**Created**: 2026-06-13

**Status**: Draft

**Input**: User description: "Operator console flagship example: modes (Plan/Build/Inspect/Review), a conversation surface, and a mode-aware view model that composes the whole kit, plus the mode-state foundations the example needs"

## Overview

The flagship example (R13, R1): an agentic **operator console** that composes
the whole component kit — task chip, task tree, parallel lanes, activity
signal, command surfaces, diff viewer, evidence panel — into one application
organized around **modes** (Plan, Build, Inspect, Review) with a persistent
**conversation surface**. It is driven by a recorded run, demonstrating the
full loop: switching modes and answering prompts flow as intents → events →
state → UI.

This feature adds two small, reusable pieces the console needs — an engine-free
**mode model** (current mode reduced from `mode_changed`, switched via a
`switch_mode` intent) and a **conversation surface** (agent/user/system
messages, clarifying questions, and approval prompts reduced from message
events) — and then assembles everything into the `operator_console` example.

Both new pieces are generic: "modes" are any named set of views, and the
conversation is any role-tagged message transcript.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Organize work with modes (Priority: P1)

An operator sees a mode strip showing Plan, Build, Inspect, and Review with the
active mode highlighted, switches modes by keyboard or command, and the console
shows the layout appropriate to that mode. The active mode is part of derived
state, and switching routes as an intent so it flows through the same
event→state loop as everything else.

**Why this priority**: Modes are the organizing skeleton of the console (R13)
and the smallest complete unit — a working mode strip that switches views is
independently useful and is what the rest of the console hangs on.

**Independent Test**: Replay a run, switch modes by key and by command, and
verify the active mode in derived state changes and the mode strip highlights
the active mode (by marker, not color alone).

**Acceptance Scenarios**:

1. **Given** the console with four modes, **When** it renders, **Then** the
   mode strip shows all modes with the active one marked distinctly (symbol +
   label, not color alone).
2. **Given** a mode shortcut, **When** the operator presses it, **Then** a
   `switch_mode` intent is delivered and the active mode in derived state
   updates (via a `mode_changed` event), and the strip re-highlights.
3. **Given** a `mode_changed` event in the stream, **When** it is reduced,
   **Then** the active mode in derived state matches it.
4. **Given** an unknown mode name in a `mode_changed` event, **When** reduced,
   **Then** the active mode is unchanged (tolerated, no crash).

---

### User Story 2 - Follow the conversation surface (Priority: P2)

An operator reads a persistent conversation transcript of agent messages, user
messages, system/status notes, clarifying questions, and approval prompts, in
order, scrolling as it grows. Each entry's role and kind are visible (agent vs
user vs system vs question vs approval), and the surface keeps the latest
entries in view.

**Why this priority**: The conversation surface (R1) is how the operator and
agent communicate; it is independently testable and reused across modes, but
the console is navigable via modes (US1) without it.

**Independent Test**: Replay a run emitting message/question/approval events,
verify each appears as a transcript entry with its role/kind, in order, and the
latest entries are visible.

**Acceptance Scenarios**:

1. **Given** message, question, and approval events, **When** the conversation
   renders, **Then** each appears as an entry tagged with its role/kind in
   arrival order.
2. **Given** a clarifying question entry, **When** it renders, **Then** it is
   visually distinct from a plain agent message (by marker/label, not color
   alone).
3. **Given** the transcript grows beyond the visible area, **When** new entries
   arrive, **Then** it scrolls to keep the latest in view.
4. **Given** an empty conversation, **When** it renders, **Then** it shows an
   explicit empty state.

---

### User Story 3 - The operator console, end to end (Priority: P1)

An operator runs the `operator_console` example: it replays a full simulated
run and, across the four modes, shows the conversation, plan/tasks, live lanes
and signal, diffs, and evidence — composed from the kit. The operator switches
modes, expands tasks, inspects a diff, reviews evidence, and invokes commands,
all keyboard-first, with public-safe rendering.

**Why this priority**: This is the deliverable the whole library has been
building toward (Principle VIII) — the demanding seed that proves the kit
composes into a real operator workbench.

**Independent Test**: Launch the example headlessly, advance the replay, switch
through all four modes, and verify each mode renders its components without
error and the run reaches completion.

**Acceptance Scenarios**:

1. **Given** the example, **When** it launches and replays the run, **Then**
   each mode renders its relevant kit components without error.
2. **Given** Build mode, **When** the run is active, **Then** the task chip,
   task tree, lanes, and activity signal reflect the replayed run.
3. **Given** Inspect mode, **When** selected, **Then** the diff viewer and
   evidence panel show the run's artifacts, public-safe by default.
4. **Given** any mode, **When** the operator uses only the keyboard, **Then**
   all primary actions (switch mode, navigate, invoke commands) are reachable.
5. **Given** the example, **When** run from a fresh checkout via documented
   steps, **Then** it starts on supported terminals (Principle VIII).

---

### Edge Cases

- A `switch_mode`/`mode_changed` to the already-active mode: no-op, no flicker.
- Mode switched while a modal (confirm/palette) is open: the modal keeps focus;
  the switch applies underneath.
- Conversation entry with an unknown role: rendered with a neutral role tag,
  never dropped or crashing.
- Very long conversation message: wrapped or truncated readably, never breaking
  layout.
- A mode with no content for the current run (e.g. Review before completion):
  shows an explicit empty/placeholder state rather than a blank pane.
- Rapid mode switching: each switch is one intent; the UI stays responsive.

## Requirements *(mandatory)*

### Functional Requirements

**Mode model (shared)**

- **FR-001**: The system MUST define a mode model with an ordered set of modes
  and a current mode, reduced from `mode_changed` events, tolerating unknown
  mode names without changing the current mode.
- **FR-002**: The system MUST expose a `switch_mode` intent (carrying the
  target mode) and a mode view model (ordered modes + which is active) for
  rendering.
- **FR-003**: A mode strip component MUST render all modes with the active one
  marked distinctly by symbol/label (not color alone), keyboard-switchable.

**Conversation surface**

- **FR-004**: The system MUST reduce conversation events (`message_added` with
  a role, `question_requested`, `approval_requested`) into an ordered
  transcript model, tolerating unknown roles.
- **FR-005**: A conversation component MUST render the transcript in order with
  each entry's role/kind visible (by marker/label, not color alone), scrolling
  to keep the latest entries visible, with an empty state.
- **FR-006**: The conversation component MUST re-render only when the
  transcript changes and stay responsive under streaming updates.

**Operator console example**

- **FR-007**: The example MUST compose the kit across the four modes: a
  conversation surface and the activity signal persistent where useful; Plan
  shows plan/tasks; Build shows the task chip, task tree, lanes, and signal;
  Inspect shows the diff viewer and evidence panel (public-safe); Review shows
  evidence.
- **FR-008**: The example MUST be driven by a committed recorded run that
  exercises tasks, work items, parallel lanes, a diff, evidence, and
  conversation/mode events.
- **FR-009**: The example MUST be fully keyboard-operable (switch modes,
  navigate, invoke commands) with public-safe rendering by default.
- **FR-010**: The example MUST run from a fresh checkout via documented steps
  on supported terminals (Principle VIII).

**Cross-cutting**

- **FR-011**: Mode switching MUST route as an intent and take effect via a
  `mode_changed` event (Principle III) — no direct UI-only mode mutation in the
  reduced state path.
- **FR-012**: New model logic (mode reduction, conversation reduction,
  selectors) MUST be engine-free and headlessly testable (Principle VII).

### Key Entities

- **Mode**: a named view (Plan, Build, Inspect, Review for the console; the
  model is agnostic to the set).
- **ModeState**: ordered modes + current mode; reduced from `mode_changed`.
- **ModeView**: ordered mode entries each with name + active flag.
- **ConversationEntry**: role (agent | user | system | unknown), kind (message
  | question | approval), text, order.
- **ConversationState / ConversationView**: ordered transcript of entries.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Switching modes by keyboard updates the active mode in derived
  state and the mode strip highlight every time (verified headlessly).
- **SC-002**: The conversation renders message/question/approval events in
  arrival order with role/kind identifiable without color (verified headlessly).
- **SC-003**: The operator console renders all four modes without error over a
  full replayed run (verified headlessly via the example).
- **SC-004**: 100% of the console's primary actions (mode switch, navigation,
  commands) are keyboard-operable.
- **SC-005**: In Inspect/Review, no unsafe value from the run's artifacts
  appears (public-safe by default), reusing the redaction from feature 004.
- **SC-006**: The example launches from a fresh checkout within the quickstart
  steps and reaches run completion.

## Assumptions

- Modes for the console are exactly Plan/Build/Inspect/Review; the mode model
  itself is agnostic to the set so other apps can define their own.
- Answering questions/approvals interactively beyond display reuses the
  existing intent + confirmation mechanisms (003/001); the conversation surface
  in this feature focuses on displaying the transcript (R1 surface), not new
  answer widgets.
- Per-mode layout is the example's concern; the library provides the mode
  model + strip and the conversation surface, not a fixed console layout.
- The example may be a new gallery entry (`operator_console`) distinct from
  `mission_control` (which stays a focused kit demo).
- Comparison/graph/session-browser views (R10/R11/R12) are out of scope; Review
  mode shows evidence, not run comparison, in this feature.
