# Feature Specification: Zero-Config Console Runner

**Feature Branch**: `009-console-runner`

**Created**: 2026-06-14

**Status**: Draft

**Input**: User description: "Zero-config console runner: a batteries-included ConsoleApp plus a watch() one-liner and an intui watch CLI that render the full kit from any canonical event stream (a JSONL file or a spawned subprocess emitting ndjson), with no application code"

## Overview

The "toothbrush" feature: make a rich console appear from a stream with **zero
code**. Today using in-TUI-tion means composing the kit by hand (~200 lines).
This adds a **batteries-included console** that renders the canonical
[event-stream contract](../008-stream-contract-packaging/) automatically, plus
two front doors:

- `watch(source)` — a one-line Python call that builds and runs the console.
- `intui watch <stream.jsonl>` / `intui watch -- <command…>` — a CLI that
  renders a captured stream file or a live subprocess that emits ndjson.

The console is a **read-mostly viewer with navigation**: it reduces the
canonical vocabulary (tasks/work-items/lanes, diff/evidence artifacts,
conversation, view routing, run lifecycle) into an activity strip, a
conversation panel, a routable central view (tasks / lanes / diff / evidence),
and a command bar — all public-safe by default and keyboard-navigable. It is
the generic substrate the market lacks: point it at any compliant producer (an
agent, a CI job, a pipeline, IntentForge) and get a console.

The full interactive operator console (modes, prompt, scripted replies) remains
the flagship *example*; this runner is the no-code generic viewer.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Render a captured stream with one command (Priority: P1)

A developer has a recorded `.jsonl` stream conforming to the contract. They run
`intui watch run.jsonl` (or `watch("run.jsonl")` in Python) and the full
console renders the replayed run — activity strip, conversation, tasks/lanes,
diffs, evidence — with no code written. They navigate views by keyboard.

**Why this priority**: This is the zero-code promise and the smallest complete
unit — a captured stream to a console with one command.

**Independent Test**: Launch the runner headlessly against a committed
canonical fixture; advance the replay; verify each canonical slice reduced and
the central views render; verify view navigation by keyboard.

**Acceptance Scenarios**:

1. **Given** a conforming `.jsonl` file, **When** `intui watch <file>` runs,
   **Then** the console renders and the run's tasks/artifacts/conversation are
   reduced and shown.
2. **Given** the running console, **When** the user routes views by command/key
   (tasks/lanes/diff/evidence), **Then** the central pane switches accordingly.
3. **Given** the stream ends, **When** replay completes, **Then** the console
   shows stream-ended health and remains interactive.
4. **Given** a `watch("run.jsonl")` call, **Then** it builds and runs the same
   console (the CLI and the one-liner share one implementation).
5. **Given** diff/evidence in the stream, **When** rendered, **Then** they are
   public-safe by default (redaction from feature 004).

---

### User Story 2 - Watch a live producer (Priority: P1)

A developer points the runner at a live command that emits the canonical stream
as ndjson on stdout: `intui watch -- <command…>`. The runner spawns the
command, consumes its output live, and the console updates as events arrive;
when the command exits, the console reflects stream end.

**Why this priority**: Live watching is the real payoff — "run your thing, see
a console." It is what makes the runner a cockpit rather than a replayer.

**Independent Test**: Spawn a tiny command that prints a few canonical ndjson
lines then exits; verify the runner consumes them into state and reflects exit.

**Acceptance Scenarios**:

1. **Given** `intui watch -- <cmd>`, **When** the command prints canonical
   ndjson lines to stdout, **Then** the console reduces them live.
2. **Given** the command emits wrapped records
   (`{"type":"run_trace_event","event":{…}}`) and a trailing non-event summary
   line, **When** consumed, **Then** events are unwrapped and reduced and the
   non-event line is ignored without error.
3. **Given** the command exits, **When** its stream closes, **Then** the
   console shows stream-ended (or disconnected on error) and stays responsive.
4. **Given** a malformed line mid-stream, **When** consumed, **Then** it is
   reported via stream health and the run continues (no crash).

---

### User Story 3 - Sensible defaults, public-safe, discoverable (Priority: P2)

The runner works with no configuration but exposes the few knobs that matter:
public-safe on/off (default on), and replay rate for files. Help/keybindings
are discoverable (footer + command bar + palette). It runs from a fresh install
on supported terminals.

**Why this priority**: "Super simple" means good defaults plus the minimum
controls; discoverability is what the market research said TUIs lack.

**Independent Test**: Run with defaults (public-safe), then with public-safe
off, and verify redaction toggles; verify the command bar/palette expose the
view actions; verify it launches from a clean install.

**Acceptance Scenarios**:

1. **Given** no options, **When** the runner starts, **Then** it renders
   public-safe with the full default layout.
2. **Given** `--no-public-safe` (trusted local), **When** rendered, **Then**
   diffs/evidence show full values.
3. **Given** the running console, **When** the user opens the command palette,
   **Then** the view actions are discoverable and runnable by keyboard.
4. **Given** a clean install (`pip install`), **When** `intui watch <file>` is
   run, **Then** it launches on a supported terminal.

---

### Edge Cases

- A stream whose events are entirely unknown types (not canonical): the console
  renders its empty states (no crash); stream health still shows progress.
- A file that does not exist / is not readable: the CLI exits with a clear error
  message, not a traceback.
- A spawned command that fails to start (not found): clear error, non-zero exit.
- A spawned command that never emits valid lines: the console shows empty states
  and stream health; quitting is always possible.
- Very large/long streams: ingestion is non-blocking; the console stays
  responsive (existing render coalescing).
- Terminal too small: the layout degrades gracefully (existing reflow).
- The runner must not require a TTY on stdin (events come from a file or the
  child's stdout pipe; the terminal stays free for the console's own input).

## Requirements *(mandatory)*

### Functional Requirements

**Batteries-included console**

- **FR-001**: The system MUST provide a `ConsoleApp` that reduces the canonical
  vocabulary (taskboard, artifacts, conversation, view routing) plus the
  recommended run-lifecycle conventions (to drive the activity strip) with no
  application-provided reducers.
- **FR-002**: The `ConsoleApp` MUST render a default layout: an activity strip,
  a conversation panel, a routable central view (tasks / lanes / diff /
  evidence), and a command bar exposing the view actions + the palette.
- **FR-003**: The console MUST be public-safe by default (diffs/evidence
  redacted), with an option to disable redaction for trusted-local use.
- **FR-004**: The console MUST be keyboard-navigable (route views, open the
  palette) with visible focus and a discoverable footer/command bar.

**Front doors**

- **FR-005**: The system MUST provide `watch(source)` that builds and runs the
  `ConsoleApp` from an event source or a stream file path, in one call.
- **FR-006**: The system MUST provide an `intui watch` CLI that accepts either a
  `.jsonl` file path (replay) or `-- <command…>` (spawn a subprocess that emits
  ndjson on stdout) and renders the console.
- **FR-007**: The CLI MUST expose `--public-safe/--no-public-safe` and a replay
  `--rate` for files; it MUST exit with a clear message (not a traceback) on a
  missing file or a command that cannot start.

**Stream ingestion**

- **FR-008**: The runner MUST accept both plain envelope lines and wrapped
  records (`{"type":"<record>","event":{…envelope…}}`), unwrapping configured
  record types and ignoring other (non-event) records (e.g. a trailing summary).
- **FR-009**: Live subprocess ingestion MUST be non-blocking and surface stream
  health (live / ended / disconnected / erroring); malformed lines MUST be
  reported via health without crashing.
- **FR-010**: The runner MUST NOT consume the terminal's stdin for events
  (events come from a file or the child process's stdout), so the console keeps
  the keyboard.

**Cross-cutting**

- **FR-011**: Stream sources (subprocess, ndjson-wrapping) MUST be engine-free
  and headlessly testable (Principle VII); the `ConsoleApp` is tested via Pilot.
- **FR-012**: The runner MUST be installable as a console entry point so
  `intui watch …` works after `pip install` (Principle VIII for adoptability).

### Key Entities

- **ConsoleApp**: the batteries-included Textual app composing the kit over the
  canonical slices; the no-code default console.
- **watch(source)**: the one-call Python entry point.
- **intui watch (CLI)**: the command-line entry point (file replay or spawn).
- **NdjsonStreamSource**: an EventSource over ndjson lines that unwraps wrapped
  records and ignores non-event records.
- **SubprocessSource**: an EventSource that spawns a command and yields its
  stdout ndjson lines live.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A conforming `.jsonl` file renders a full console with **one
  command** and **zero application code** (verified headlessly + documented).
- **SC-002**: A live subprocess emitting canonical ndjson is reduced into the
  console as events arrive, and exit is reflected as stream end (verified).
- **SC-003**: Wrapped records are unwrapped and trailing non-event records are
  ignored without error (verified headlessly).
- **SC-004**: Diffs/evidence render public-safe by default; `--no-public-safe`
  shows full values (verified).
- **SC-005**: 100% of console navigation is keyboard-operable; a missing
  file/uncstartable command yields a clear message, not a traceback.
- **SC-006**: After a clean `pip install`, `intui watch <file>` launches on a
  supported terminal.

## Assumptions

- The runner consumes the **canonical** vocabulary (feature 008). Producers
  whose names differ (e.g. IntentForge's `case_started`/`file_diff`) are
  normalized by an adapter — the IntentForge adapter is the *next* feature and
  is out of scope here; this runner is demoed against a canonical fixture.
- Live input is a spawned subprocess's stdout or a file — **not** piped stdin
  (a full-screen TUI needs the terminal for its own keyboard input).
- The default console is a read-mostly viewer (navigation, no prompt/modes); the
  full interactive operator console stays the flagship example.
- "Spawn a subprocess" runs a user-provided command and reads its stdout; it is
  not a sandbox and inherits the user's environment (the user chose the command).
- `--follow` (tailing a growing file) and richer process controls are out of
  scope; file-replay + subprocess-spawn cover the toothbrush case.
