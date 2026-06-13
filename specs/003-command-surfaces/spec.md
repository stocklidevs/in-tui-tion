# Feature Specification: Command Surfaces

**Feature Branch**: `003-command-surfaces`

**Created**: 2026-06-12

**Status**: Draft

**Input**: User description: "Command surfaces: a shared command registry feeding an always-visible bottom command menu and a searchable command palette, emitting intents with risky-action confirmation and availability from derived state"

## Overview

The interaction layer of the component kit (R7): a way for users to invoke
actions. An application declares its actions once as a **command registry** —
each command has a stable id, a human label, an optional key, the intent it
emits, a risky flag, and an availability rule over current state. Two
components render that one registry: an always-visible **bottom command menu**
of the primary actions, and a searchable **command palette** overlay for
finding and running any command by name.

Both surfaces are generic: a "command" is any named action (approve a plan,
open a diff, switch a view, run a job). Commands emit intents through the
foundation's existing action seam, so invoking one never mutates application
state directly, and risky commands route through the confirmation flow already
shipped in feature 001. Availability is data-driven from derived state, so
commands disable themselves when they don't apply.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Invoke primary actions from the bottom menu (Priority: P1)

A developer places a bottom command menu in their TUI listing the primary
actions. An end user sees the always-visible menu with each action's key and
label, presses the key (or clicks) to invoke it, and unavailable actions
appear disabled rather than firing.

**Why this priority**: The bottom menu is the single most recognizable
operator affordance (R7) and the smallest complete unit — a working menu that
invokes intents is independently useful, and it establishes the command
registry the palette reuses.

**Independent Test**: Register a handful of commands, render the menu, press a
command's key, and verify the corresponding intent reaches the app handler;
verify a command whose availability rule is false renders disabled and does
not fire.

**Acceptance Scenarios**:

1. **Given** a registry with several commands, **When** the bottom menu
   renders, **Then** it shows each primary command's key and label in a
   compact always-visible row.
2. **Given** a command bound to a key, **When** the user presses that key,
   **Then** the command's intent is delivered to the app handler with its
   declared payload (no direct state mutation).
3. **Given** a command marked risky, **When** the user invokes it, **Then**
   the built-in confirmation prompt appears before the intent is delivered,
   and cancelling it delivers nothing.
4. **Given** a command whose availability rule evaluates false for the
   current state, **When** the menu renders, **Then** that command is shown
   disabled and pressing its key does nothing.
5. **Given** the available commands change as state changes, **When** state
   updates, **Then** the menu's enabled/disabled rendering updates without
   other menu items being disturbed.
6. **Given** more primary commands than fit the width, **When** the menu
   renders, **Then** it shows as many as fit plus an explicit overflow
   affordance (e.g. a "more" entry opening the palette) rather than clipping.

---

### User Story 2 - Find and run any command from the palette (Priority: P2)

An end user opens a command palette (a keyboard shortcut), types to filter
the full command list by name or label, navigates the filtered results with
the keyboard, and runs the selected command. The palette closes and the
command is invoked exactly as if triggered from the menu.

**Why this priority**: The palette makes the full command set discoverable
and reachable without memorizing keys (the Grok-like slash/command model from
the requirements doc). It depends on the same registry US1 establishes but is
independently testable.

**Independent Test**: Open the palette, type a query, verify the result list
filters, select an entry with the keyboard, and verify the same intent is
delivered (and risky confirmation still applies).

**Acceptance Scenarios**:

1. **Given** a registry of commands, **When** the user opens the palette,
   **Then** all commands are listed with their labels and keys (available
   ones runnable, unavailable ones shown disabled).
2. **Given** the open palette, **When** the user types a query, **Then** the
   list filters to commands whose id or label matches, ranked by match
   quality, updating as they type.
3. **Given** a filtered list, **When** the user moves the selection with the
   keyboard and confirms, **Then** the selected command is invoked (its
   intent delivered, risky confirmation applied) and the palette closes.
4. **Given** the open palette, **When** the user dismisses it (escape),
   **Then** it closes and no command is invoked.
5. **Given** a query matching nothing, **When** results are empty, **Then**
   the palette shows an explicit empty state rather than appearing broken.

---

### Edge Cases

- A command's key colliding with an application binding: command keys are
  scoped to the menu's focus / resolved deterministically, never silently
  shadowing unrelated bindings.
- Duplicate command ids in a registry: rejected at registration with a clear
  error (ids are the stable identity).
- Invoking a command that became unavailable between render and key press:
  the invocation is rejected (re-checked at fire time), not delivered stale.
- Palette query with mixed case / partial words: matching is case-insensitive
  and subsequence-friendly.
- Empty registry: the menu shows an explicit empty state; the palette opens to
  its empty state.
- Very long command labels: truncated in the menu, shown in full in the
  palette.
- A command with no key: absent from key-driven invocation but still runnable
  from the palette.

## Requirements *(mandatory)*

### Functional Requirements

**Command registry (shared model)**

- **FR-001**: The system MUST define a Command with a stable id, a label, an
  optional key, the intent it emits (name + payload + risky flag), and an
  availability rule evaluated against current state.
- **FR-002**: The system MUST provide a registry that holds commands, rejects
  duplicate ids, and exposes the ordered command list and per-command
  availability for a given state.
- **FR-003**: Availability MUST be derived from state (a predicate/selector),
  re-evaluated as state changes, with no side effects.
- **FR-004**: Both surfaces MUST consume the same registry — a command
  declared once is reachable from menu and palette identically.

**Bottom command menu**

- **FR-005**: The menu MUST render the primary commands as an always-visible,
  compact row showing each command's key and label.
- **FR-006**: The menu MUST invoke a command by key press and by mouse click,
  delivering the command's intent through the application action seam (never
  mutating application state directly).
- **FR-007**: Unavailable commands MUST render visibly disabled and MUST NOT
  fire when their key is pressed.
- **FR-008**: When primary commands exceed the available width, the menu MUST
  show an overflow affordance (opening the palette) instead of clipping.

**Command palette**

- **FR-009**: The palette MUST open via a keyboard shortcut and list all
  commands with labels and keys, marking unavailable ones disabled.
- **FR-010**: The palette MUST filter commands by a typed query against id and
  label, case-insensitively and subsequence-friendly, ranked by match
  quality, updating as the user types.
- **FR-011**: The palette MUST support keyboard selection and confirmation,
  invoke the selected command (delivering its intent), and then close.
- **FR-012**: The palette MUST be dismissable without invoking anything, and
  MUST show an explicit empty state when no command matches.

**Cross-cutting**

- **FR-013**: Risky commands MUST route through the confirmation flow from
  feature 001 before their intent is delivered, from both surfaces.
- **FR-014**: A command invoked when unavailable (availability changed since
  render) MUST be rejected at fire time, not delivered.
- **FR-015**: Both surfaces MUST be fully keyboard-operable with visible
  focus, and every command identity in the UI MUST be readable without relying
  on color alone (Principle IV).
- **FR-016**: Both surfaces MUST re-render only when their inputs (registry,
  availability, query, selection) change, staying responsive under streaming
  state updates.
- **FR-017**: The feature MUST extend the examples gallery so a runnable
  example demonstrates the menu and palette invoking real intents with at
  least one risky command (Principle VIII).

### Key Entities

- **Command**: id, label, optional key, intent template (name, payload,
  risky), availability rule; the unit both surfaces render.
- **CommandRegistry**: ordered collection of commands keyed by id; resolves
  availability for a state and rejects duplicate ids.
- **CommandView**: derived per-state projection both surfaces consume — each
  command with its current enabled/disabled status.
- **PaletteState**: the palette's transient UI state (query, filtered+ranked
  results, selection); local UI state, not application state.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A developer can declare a command once and have it appear in
  both the menu and the palette with no duplicated definition.
- **SC-002**: 100% of commands are invocable by keyboard alone (menu key or
  palette selection), with visible focus throughout.
- **SC-003**: Invoking a risky command from either surface always presents
  confirmation before any intent is delivered (verified headlessly for both
  surfaces).
- **SC-004**: Typing a 3+ character query in the palette narrows a 20-command
  registry to matching results within one render frame.
- **SC-005**: An unavailable command never delivers an intent, whether invoked
  from the menu key, a click, or the palette (verified for all three paths).
- **SC-006**: Every command's identity is distinguishable with color disabled
  (key + label text, not color).

## Assumptions

- Commands emit the existing `Intent` type and flow through the app's
  `post_intent` / confirmation flow from feature 001 — this feature adds the
  registry and the two surfaces, not a new action mechanism.
- The exact opener shortcut for the palette and the default key-display style
  are plan-phase decisions; the requirement is keyboard-openable and
  keyboard-operable.
- The initial action set from the requirements doc (Interrupt, Cancel,
  Approve, Tasks, Diff, Files, Evidence, Compare, Graph, Help) is illustrative
  for the example; the components are agnostic to which commands exist.
- Whether the palette is backed by the engine's built-in palette or a custom
  overlay is a plan-phase decision; behavior in this spec governs either way.
- "Slash vs colon" command syntax in the palette is cosmetic; matching works
  on plain typed text. Slash-command parsing in the conversation surface is a
  later feature.
- Multi-key chords and command arguments (beyond a static payload) are out of
  scope for this feature.
