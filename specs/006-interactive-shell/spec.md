# Feature Specification: Interactive Shell & Activity Strip

**Feature Branch**: `006-interactive-shell`

**Created**: 2026-06-13

**Status**: Draft

**Input**: User description: "Interactive shell and signature activity strip: a persistent prompt input that submits text as an intent and a user message, and a prominent full-width KITT-style activity strip color-coded by run state, wired into the operator console"

## Overview

Two additions that turn the operator console from a run *viewer* into a live
*command center*: a persistent **prompt surface** the operator types into (R1's
input half, which the read-only conversation log never provided), and the
signature **activity strip** — the prominent, full-width, KITT-style swooshing
indicator color-coded by overall run state (R6's marquee ambient signal, which
so far has only appeared as small per-component indicators).

The prompt surface closes the interaction loop: typing a goal and submitting it
emits a `prompt_submitted` intent and appends a `user` message to the
conversation transcript — so what you type immediately appears in the same
data-driven surface everything else flows through. The activity strip is a
preset of the existing Signal primitive: a wide indicator bound to an
app-level activity-state selector, sweeping in the state's color.

Both are generic: the prompt is any single-line natural-language input that
emits an intent; the activity strip is any full-width status indicator bound to
a state field.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Type and submit a prompt (Priority: P1)

An operator types a natural-language goal into a persistent prompt field at the
bottom of the console and submits it (Enter). The submitted text immediately
appears in the conversation as a `user` message, and a `prompt_submitted`
intent is delivered to the application. The field clears, ready for the next
input, and stays keyboard-focusable at all times.

**Why this priority**: This is the missing input half of R1 — the difference
between watching a conversation and driving one. It is the smallest complete
interactive unit and is independently useful.

**Independent Test**: Type text into the prompt, press Enter, and verify a
`prompt_submitted` intent is delivered with the text, the field clears, and (when
wired to the conversation) the text appears as a user entry.

**Acceptance Scenarios**:

1. **Given** the prompt field, **When** the operator types text and presses
   Enter, **Then** a `prompt_submitted` intent carrying that text is delivered
   to the application and the field clears.
2. **Given** an empty or whitespace-only prompt, **When** Enter is pressed,
   **Then** no intent is delivered (nothing submitted).
3. **Given** the console wired to append the submission, **When** a prompt is
   submitted, **Then** it appears in the conversation transcript as a `user`
   message in order.
4. **Given** the prompt field, **When** the operator navigates the rest of the
   console by keyboard and returns, **Then** the prompt is reachable/focusable
   again without a mouse.
5. **Given** a submitted prompt, **When** the application responds (appends
   agent messages/events), **Then** those appear in the conversation as usual —
   the prompt surface does not special-case the response.

---

### User Story 2 - See overall state at a glance with the activity strip (Priority: P1)

An operator sees a prominent, full-width activity strip across the top of the
console whose color and motion reflect the overall run state — sweeping red
while the agent is thinking/working, amber while awaiting input, cyan during
verification, steady green when passed, violet while reviewing history, and a
fast red strobe on failure. The state is data-driven, and the strip always
shows a textual state label alongside (not color alone).

**Why this priority**: The KITT-style ambient signal is R6's signature element
and the project's visual identity; making it the prominent, app-level indicator
(not just small per-component dots) is what makes the console feel alive.

**Independent Test**: Drive an activity-state field through its values and
verify the strip's color/motion and its textual label change with each state,
distinguishable without color.

**Acceptance Scenarios**:

1. **Given** an activity-state field, **When** it is `thinking`/working, **Then**
   the strip sweeps (swoosh) in the thinking color with a textual label.
2. **Given** the field transitions across states (working → waiting →
   verifying → passed → failed), **Then** the strip's color, motion, and label
   update per state (failure shows the fast strobe).
3. **Given** color is disabled, **When** the strip renders, **Then** the current
   state is still identifiable from its textual label/glyph.
4. **Given** the strip spans the available width, **When** the terminal is
   resized, **Then** it reflows to the new width without breaking layout.

---

### User Story 3 - Drive the operator console live (Priority: P1)

The `operator_console` example gains the prompt surface and the activity strip:
the strip is the headline element across the top, reflecting the replayed run's
state; the prompt sits persistently at the bottom. Submitting a prompt appends
it to the conversation and the console acknowledges it (a scripted agent reply,
since there is no live backend yet), with the activity strip flashing the
working state while it "responds."

**Why this priority**: This is where the two pieces become real (Principle VIII)
and the console finally feels operable rather than replay-only.

**Independent Test**: Launch the example, submit a prompt, and verify it appears
in the conversation, the activity strip reflects the run/working state, and the
console remains responsive and keyboard-operable.

**Acceptance Scenarios**:

1. **Given** the example, **When** it runs, **Then** the activity strip is a
   prominent full-width element reflecting the run's current state.
2. **Given** the example, **When** the operator submits a prompt, **Then** it
   appears as a user message and the console acknowledges it (scripted reply),
   with the strip showing the working state during the response.
3. **Given** the example, **When** operated by keyboard only, **Then** prompt
   submission, mode switching, and navigation all work.
4. **Given** a fresh checkout, **When** the example is run via documented steps,
   **Then** it starts on supported terminals (Principle VIII).

---

### Edge Cases

- Submitting while a modal (confirm/palette) is open: the modal keeps focus;
  the prompt does not steal it.
- Very long prompt text: handled by the input (scrolls within the field); the
  resulting conversation entry wraps/truncates readably.
- Rapid successive submissions: each is its own intent; order is preserved in
  the transcript.
- Activity state with an unknown value: the strip falls back to a neutral
  steady state with the raw label, never blank or crashing.
- Prompt submitted with no application handler wired: no crash; the intent is
  simply undelivered (or delivered to a no-op handler).
- Activity strip in a very narrow terminal: shows a shortened track plus the
  label rather than clipping the label.

## Requirements *(mandatory)*

### Functional Requirements

**Prompt surface**

- **FR-001**: The system MUST provide a persistent single-line prompt input
  that, on submit (Enter), emits a `prompt_submitted` intent carrying the typed
  text and then clears.
- **FR-002**: The prompt MUST NOT submit empty or whitespace-only input.
- **FR-003**: The prompt MUST be keyboard-focusable and operable without a
  mouse; submission MUST NOT require leaving the keyboard.
- **FR-004**: The prompt component MUST route submission as an intent only
  (Principle III) — it MUST NOT itself mutate application state or the
  conversation; appending the user message is the application's responsibility.
- **FR-005**: The system SHOULD provide a helper to build the user-message
  event for a submitted prompt, so applications can append it in one step.

**Activity strip**

- **FR-006**: The system MUST provide a full-width activity strip bound to a
  state field, rendering the KITT-style swoosh and the R6 state colors
  (thinking, waiting, verifying, passed/success, history, failure) with the
  failure state using the fast strobe.
- **FR-007**: The activity strip MUST display a textual state label alongside
  the visual, so state is identifiable without color (Principle IV).
- **FR-008**: The activity strip MUST reflow to the available width on resize
  and degrade to a shortened track plus label in narrow terminals.
- **FR-009**: An unknown activity-state value MUST render a neutral steady
  fallback with the raw label, never blank or crashing.

**Operator console integration**

- **FR-010**: The `operator_console` example MUST feature the activity strip as
  a prominent full-width element reflecting the run's overall state, and the
  prompt surface persistently at the bottom.
- **FR-011**: Submitting a prompt in the example MUST append it to the
  conversation as a user message and produce a scripted acknowledgement
  (agent reply), with the activity strip showing the working state during it.
- **FR-012**: The example MUST remain fully keyboard-operable and run from a
  fresh checkout (Principle VIII).

**Cross-cutting**

- **FR-013**: Both components MUST re-render only when their bound inputs change
  (the strip) or on interaction (the prompt), staying responsive under
  streaming updates.
- **FR-014**: Any new model/helper logic (e.g. activity-state mapping, the
  user-message event helper) MUST be engine-free and headlessly testable
  (Principle VII).

### Key Entities

- **PromptInput**: a single-line input that emits a `prompt_submitted` intent
  with the typed text and clears on submit.
- **ActivityStrip**: a full-width status indicator (a preset of the Signal
  primitive) bound to an activity-state field, with the R6 color/motion mapping
  and a textual label.
- **ActivityState**: the overall run state value the strip binds to (thinking,
  waiting, verifying, passed, history, failure, idle).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Submitting a non-empty prompt always delivers exactly one
  `prompt_submitted` intent with the text and clears the field (verified
  headlessly); empty/whitespace submits deliver none.
- **SC-002**: A submitted prompt appears in the conversation transcript as a
  user message in order (verified in the example).
- **SC-003**: The activity strip reflects every activity state with a distinct
  color/motion AND a distinct textual label; states are distinguishable with
  color disabled (verified headlessly).
- **SC-004**: 100% of the prompt and console interactions are keyboard-operable.
- **SC-005**: The activity strip reflows across terminal widths without clipping
  its label.
- **SC-006**: The example runs from a fresh checkout and a submitted prompt is
  acknowledged within the running session.

## Assumptions

- There is no live agent backend yet; the example's response to a submitted
  prompt is scripted. The interaction loop (input → intent → user message →
  agent reply events → transcript) is real and reusable; only the agent is
  simulated until the IntentForge adapter lands.
- The activity strip reuses the existing Signal primitive and theme status
  colors from features 001/004; this feature adds the full-width preset and the
  R6 state mapping, not a new motion engine.
- The activity-state field is supplied by the application (e.g. reduced from run
  events); the strip is agnostic to how it is produced.
- Multi-line prompt input, input history/recall, and slash-command parsing in
  the prompt are out of scope (later); submission is single-line text.
- The prompt emits a generic `prompt_submitted` intent; mapping that to real
  work is the application/adapter's concern.
