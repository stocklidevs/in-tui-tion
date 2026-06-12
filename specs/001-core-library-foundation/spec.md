# Feature Specification: Core Library Foundation

**Feature Branch**: `001-core-library-foundation`

**Created**: 2026-06-12

**Status**: Draft

**Input**: User description: "Core library foundation: state-driven component model, event/reducer/view-model pipeline, theming, and a minimal runnable example"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Build a TUI from structured state (Priority: P1)

A Python developer wants to build a terminal application without managing raw
terminal output or parsing logs. They describe their application's facts as a
stream of events, declare how those events reduce into application state, and
compose widgets that render views of that state. When new events arrive, the
visible UI updates automatically — the developer never imperatively repaints
the screen.

**Why this priority**: This is the library's reason to exist. The
event → state → view → widget pipeline is the foundation every other layer
(component kit, examples, adapters) builds on. Nothing else can be delivered
without it.

**Independent Test**: Can be fully tested by writing a small application that
feeds a scripted sequence of events into the pipeline and verifying the
rendered terminal output reflects each state change, with no direct
screen-drawing code in the application.

**Acceptance Scenarios**:

1. **Given** a developer has declared event types, a reducer, and a widget
   bound to a view of the state, **When** the application starts with an empty
   event stream, **Then** the widget renders the declared initial state.
2. **Given** a running application, **When** a new event is appended to the
   stream, **Then** the state store updates and every widget bound to the
   affected view re-renders, without any other widget being disturbed.
3. **Given** a running application, **When** an event arrives whose type the
   reducer does not recognize, **Then** the event is retained in the stream,
   the state is unchanged, and the application neither crashes nor blanks.
4. **Given** a developer reads the getting-started documentation, **When**
   they follow it from a fresh checkout, **Then** they reach a running example
   application using only documented steps.

---

### User Story 2 - Replay a recorded session, test headlessly (Priority: P2)

A developer (or an automated test) wants to verify application behavior
without a live source or an interactive terminal. They load a recorded event
stream from a file and either replay it through the visible UI or feed it
through the pipeline headlessly, asserting on the resulting state and view
models.

**Why this priority**: Replayability is a constitutional requirement
(Principle VII) and the cheapest way to develop, demo, and regression-test
everything that follows. It also proves the pipeline is genuinely decoupled
from rendering.

**Independent Test**: Can be fully tested by recording an event stream,
replaying it twice (once headless, once rendered), and verifying both produce
identical final state snapshots.

**Acceptance Scenarios**:

1. **Given** a recorded event stream file, **When** it is replayed through the
   pipeline headlessly, **Then** the final state snapshot equals the snapshot
   produced by a live run of the same events.
2. **Given** the same recorded stream replayed multiple times, **When** final
   states are compared, **Then** they are identical (replay is deterministic).
3. **Given** a recorded stream from an older envelope version that the library
   still supports, **When** it is replayed, **Then** events are interpreted
   correctly according to their declared version.
4. **Given** a malformed event in a recorded stream, **When** the stream is
   replayed, **Then** the library reports which event failed and why, and the
   developer can choose to skip it or halt.

---

### User Story 3 - React to user input through intents (Priority: P2)

An end user of a TUI built with the library navigates with the keyboard
(mouse where natural) and triggers actions — select, toggle, confirm. Each
action is delivered to the application as a named intent; the application
responds by appending new events, which flow back through the pipeline and
update the UI.

**Why this priority**: Without input, the foundation only supports passive
viewers. Intent-based actions close the unidirectional loop and are required
by Principle III before any interactive component can be built.

**Independent Test**: Can be fully tested by simulating key presses against a
running application and verifying the application receives the corresponding
named intents, and that events it appends in response update the UI.

**Acceptance Scenarios**:

1. **Given** a widget with a bound action, **When** the user activates it via
   its keyboard shortcut, **Then** the application receives a named intent
   carrying the action's declared payload — no library code mutates
   application state directly.
2. **Given** an action declared as risky, **When** the user triggers it,
   **Then** the library requires an explicit confirmation step before the
   intent is delivered.
3. **Given** any primary action in the running example, **When** a user
   attempts it with keyboard only, **Then** it is reachable and operable
   without a mouse.

---

### User Story 4 - Theme and signal with meaning (Priority: P3)

A developer applies a theme (colors, emphasis, status palette) across their
application, and binds status-driven visual signals (such as an animated
activity indicator) to fields of the application state. When the state
changes, the signal's appearance changes accordingly; every color-coded
status also has a textual or symbolic counterpart.

**Why this priority**: Theming and data-driven motion are part of the
library's "rich, first-class" identity (Principle V), but they decorate the
pipeline rather than enable it — the foundation is viable for one release
without them being complete.

**Independent Test**: Can be fully tested by switching themes at runtime and
by driving a status field through its states, verifying the bound signal and
its textual counterpart update with each transition.

**Acceptance Scenarios**:

1. **Given** an application using the default theme, **When** the developer
   swaps in another theme, **Then** all themed widgets reflect the new palette
   without code changes to the widgets themselves.
2. **Given** a status signal bound to a state field, **When** the field
   transitions (e.g., working → waiting → succeeded → failed), **Then** the
   signal's color and motion change per transition, and a textual/symbolic
   indicator changes with it.
3. **Given** a terminal with reduced color support, **When** the application
   runs, **Then** it degrades gracefully and status remains distinguishable
   without color.

---

### Edge Cases

- Events arriving faster than the renderer can draw: the UI MUST remain
  responsive, coalescing renders rather than queuing unbounded work.
- Terminal resized (including very small sizes): layout reflows; content that
  cannot fit is clipped or scrollable, never crashing.
- Event stream source disconnects or ends mid-run: the UI shows stream health
  and retains the last known state for inspection.
- Two events with the same event ID: duplicates are detected and ignored,
  preserving append-only semantics.
- An application's reducer raises an error on an event: the library isolates
  the failure, reports it, and keeps the UI alive with the prior state.
- Running on Windows, macOS, Linux, and WSL terminals with differing
  capabilities: features degrade gracefully (per constitution) rather than
  failing.

## Requirements *(mandatory)*

### Functional Requirements

**Event pipeline**

- **FR-001**: The library MUST accept application facts as events in a
  versioned envelope carrying at minimum: schema version, unique event ID,
  timestamp, event type, and scope identifiers.
- **FR-002**: The library MUST treat the event stream as append-only:
  consumed events are never mutated or removed, and duplicate event IDs are
  ignored.
- **FR-003**: The library MUST let applications declare reducers that fold
  events into a current state snapshot, and MUST produce identical snapshots
  for identical event sequences (deterministic reduction).
- **FR-004**: The library MUST support deriving view models from state, so
  widgets consume presentation-shaped data rather than raw state or events.
- **FR-005**: The pipeline (events → state → view models) MUST be usable
  headlessly, with no terminal attached, for testing and tooling.
- **FR-006**: The library MUST support recording an event stream to a file
  and replaying it later through the same pipeline, with identical results.
- **FR-007**: The library MUST surface stream health (live, ended,
  disconnected, erroring) as part of derived state.
- **FR-008**: The library MUST isolate application reducer failures: a
  failing event is reported with its ID and cause, and the UI continues with
  the last good state.

**Component model and rendering**

- **FR-009**: The library MUST provide a component model where widgets bind
  to view models and re-render automatically when their bound data changes.
- **FR-010**: Widgets MUST NOT hold authoritative application state, parse
  logs, or read application files directly; their only inputs are view models
  and user interaction.
- **FR-011**: The library MUST provide foundational layout capabilities
  (vertical/horizontal arrangement, sizing, scrolling) sufficient to compose
  a full-screen application from multiple widgets.
- **FR-012**: Rendering MUST NOT block on event ingestion or application
  work: the UI remains responsive while events stream in.
- **FR-013**: The library MUST handle terminal resize, reduced color depth,
  and missing capabilities by degrading gracefully rather than crashing.

**Actions and input**

- **FR-014**: The library MUST deliver user interactions to the application
  as named intents with declared payloads; library code MUST NOT mutate
  application state or perform file/process manipulation on the
  application's behalf.
- **FR-015**: Every primary action MUST be reachable by keyboard; mouse
  support MAY supplement but never replace keyboard paths.
- **FR-016**: Actions declared risky MUST require an explicit confirmation
  step before the intent is delivered.

**Theming and signals**

- **FR-017**: The library MUST support application-wide themes (palette,
  emphasis, status colors) switchable without modifying widget code, and MUST
  ship with at least one default theme.
- **FR-018**: The library MUST provide status-driven signal primitives whose
  appearance (color, motion) is bound to state fields, and every color-coded
  status MUST have a textual or symbolic counterpart.

**Example and documentation**

- **FR-019**: The feature MUST include at least one runnable example
  application that replays a recorded event stream and demonstrates the
  pipeline, component model, input intents, and theming together.
- **FR-020**: The example MUST run from a fresh checkout using documented
  steps, on Windows, macOS, Linux, and WSL terminals.

### Key Entities

- **Event**: An append-only fact in a versioned envelope — version, event ID,
  timestamp, type, scope (e.g., session/task/lane identifiers), summary, and
  payload.
- **Event Stream**: An ordered, append-only sequence of events from a live
  source or a recording; carries health status.
- **State Snapshot**: The current application state produced by reducing the
  stream; deterministic for a given event sequence.
- **Reducer**: Application-declared logic folding one event into state.
- **View Model**: Presentation-shaped projection of state consumed by
  widgets.
- **Widget/Component**: A renderable unit bound to a view model; composes
  into layouts; never holds authoritative state.
- **Intent (Action)**: A named, validated user-triggered request delivered to
  the application; may be flagged risky (requiring confirmation).
- **Theme**: A named set of palette/emphasis/status-color definitions applied
  application-wide.
- **Signal**: A status-driven visual primitive (color + motion + textual
  counterpart) bound to a state field.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A developer following the getting-started documentation reaches
  the running example from a fresh checkout in under 10 minutes.
- **SC-002**: Replaying the same recorded event stream produces an identical
  final state snapshot in 100% of runs (verified across at least 3 platforms:
  Windows, Linux/WSL, macOS where available).
- **SC-003**: The UI remains responsive (visible updates continue, input is
  accepted) while ingesting a recorded stream of at least 1,000 events played
  back at 100 events/second.
- **SC-004**: 100% of primary actions in the example application are operable
  with keyboard alone.
- **SC-005**: All pipeline behavior (reduction, view models, replay, error
  isolation) is verified by automated headless tests that run without any
  terminal — zero terminal-dependent tests for core logic.
- **SC-006**: Every status conveyed by color in the example is also
  identifiable with color disabled.

## Assumptions

- The first example is a small, self-contained demo (e.g., replaying a sample
  recorded run) — the full agentic operator console and IntentForge adapter
  are later features, as is the high-level component kit (task chips, lanes,
  diff viewers, evidence panels).
- Live external event sources (attaching to a running process, network
  streams) are out of scope; this feature covers in-process sources and
  file-based recordings, with the source interface designed so live sources
  can be added later.
- Recording format details (file layout, compression) follow reasonable
  defaults; the only hard requirement is versioned envelopes and lossless
  replay.
- "Risky action" classification is declared by the application, not inferred
  by the library.
- Performance targets assume typical developer hardware and common modern
  terminal emulators (Windows Terminal, macOS Terminal/iTerm2, common Linux
  terminals).
- Public-safety filtering (Principle VI) applies to evidence-rendering
  components in the future component kit; the foundation only needs to carry
  artifact/payload metadata (such as a public-safety flag) through the
  pipeline without stripping it.
