# Feature Specification: IntentForge Adapter

**Feature Branch**: `010-intentforge-adapter`

**Created**: 2026-06-14

**Status**: Draft

**Input**: User description: "A thin adapter that normalizes IntentForge's
run-trace event stream (`{sequence,name,payload}` records + a trailing summary)
into the canonical in-TUI-tion vocabulary, so `intui watch` renders a real IF
benchmark run with no IF-specific code in the console."

## Overview

Feature 009 built a zero-config console that consumes the **canonical** event
vocabulary. IntentForge (IF) — the flagship real-data consumer — emits a
*different* shape: `intentforge … --event-stream ndjson` prints lines of
`{"type":"run_trace_event","event":{"sequence":N,"name":"<slug>","payload":{…}}}`
and a final `{"type":"summary","summary":{…}}`. The inner record is **not** an
intui envelope (no `version`/`event_id`/`run_id`/`timestamp`/`scope`).

This feature is the **thin normalizer**: a pure, engine-free function that maps
each IF run-trace record (and the summary) to a canonical envelope, plus an
`IntentForgeSource` that wires it onto a file replay or a live `intentforge`
subprocess, and an `--adapter intentforge` switch on `intui watch`. The result:
point the runner at a real IF run and get a console — no IF-specific code in the
console or the kit.

IF's name→canonical mapping (verified against the IF repo, 2026-06-14):

| IF event `name` | canonical `type` | scope / payload |
|---|---|---|
| `matrix_suite_started` | `run_started` | — (run lifecycle → activity strip) |
| `matrix_suite_finished` | `run_completed` | `status` |
| `case_started` | `task_started` | `task_id = case_id`; index/total |
| `case_finished` | `task_completed` | `task_id = case_id`; `status` (failed→failed) |
| `assembly_item_started` | `work_item_started` | `work_item_id = case_id` |
| `assembly_item_committed` | `work_item_completed` | `work_item_id`; status completed |
| `assembly_item_failed` | `work_item_completed` | `work_item_id`; `status` failed |
| `assembly_plan_blocked` | `task_blocked` | `task_id = case_id` (blueprint id) |
| `file_diff` | `diff_ready` | `unified = payload.diff` (parsed by the kit) |
| `repeat_started` / `repeat_finished` | `message_added` | a conversation line (visibility) |
| (trailing) `summary` | `evidence_ready` | metrics from the summary payload |

IF already redacts its payloads (public-safe diffs, no abs paths/secrets), so the
adapter forwards diffs as-is and the console's default redaction stays on.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Render a captured IF run with one command (Priority: P1)

A developer has a captured IF stream file (the output of
`intentforge assembly-benchmark … --event-stream ndjson > run.ndjson`). They run
`intui watch --adapter intentforge run.ndjson` and the console renders the
benchmark: cases as tasks, assembly items as work items, file diffs in the diff
view, the run lifecycle on the activity strip, and the final summary as evidence
— with no IF-specific code.

**Why this priority**: This is the headline payoff — a real IF run becomes a
console through one switch, proving the canonical-contract strategy end to end.

**Independent Test**: Run the adapter over a committed IF-shaped fixture
(headless) and assert each canonical slice is reduced (taskboard, work items,
diff, evidence, run-status); render it through `ConsoleApp` via Pilot.

**Acceptance Scenarios**:

1. **Given** a captured IF ndjson stream, **When** `intui watch --adapter
   intentforge <file>` runs, **Then** cases→tasks, assembly items→work items,
   file_diff→diff view, and matrix lifecycle→activity state are all reduced.
2. **Given** the trailing `summary` record, **When** consumed, **Then** it
   becomes an evidence artifact shown in the evidence view.
3. **Given** an IF `file_diff` carrying a unified diff, **When** rendered,
   **Then** the diff view shows the changed file(s), public-safe by default.
4. **Given** a `case_finished` with `status: "failed"`, **When** reduced,
   **Then** the corresponding task shows a failed status.

---

### User Story 2 - Watch a live IntentForge run (Priority: P1)

A developer runs `intui watch --adapter intentforge -- intentforge
assembly-benchmark … --event-stream ndjson`. The runner spawns IF, adapts its
stdout live, and the console updates as the benchmark progresses; when IF exits,
the console reflects stream end.

**Why this priority**: Watching a live IF benchmark is the real cockpit use
case and the reason the adapter exists.

**Independent Test**: Spawn a tiny producer that prints a few IF-shaped ndjson
lines then exits; verify the adapter reduces them live and exit is reflected.

**Acceptance Scenarios**:

1. **Given** `--adapter intentforge -- <cmd>`, **When** the command prints IF
   run-trace ndjson, **Then** the console reduces the adapted canonical events.
2. **Given** IF exits, **When** its stream closes, **Then** the console shows
   stream-ended and stays responsive.
3. **Given** a record the adapter does not map (an unknown IF `name`), **When**
   consumed, **Then** it is skipped without crashing and the run continues.

---

### User Story 3 - Adapter is reusable from Python (Priority: P2)

A developer wires the adapter in code: `watch(IntentForgeSource("run.ndjson"))`
or calls the pure `adapt_record(record, run_id=…)` to normalize a single IF
record in their own pipeline/tests.

**Why this priority**: The pure function is the testable core and lets others
embed IF normalization without the CLI.

**Independent Test**: Call `adapt_record` on each IF event shape and assert the
returned canonical envelope (type, scope, payload); assert unmapped/blank inputs
return `None`.

**Acceptance Scenarios**:

1. **Given** an IF wrapper record or its inner `{sequence,name,payload}`,
   **When** `adapt_record` is called, **Then** it returns a valid canonical
   `Event` (or `None` for an ignored/unknown record).
2. **Given** `IntentForgeSource(<path>)`, **When** passed to `watch`/
   `build_console`, **Then** it renders like any other source.
3. **Given** the adapter output, **When** validated with `validate_stream`/
   `validate_event` against `KNOWN_EVENT_TYPES`, **Then** there are no envelope
   errors.

---

### Edge Cases

- A `file_diff` whose `diff` is missing or empty (IF's sanitizer can drop a blob
  containing `100.`/paths/secrets): the adapter still emits `diff_ready` with an
  empty/parsed-empty diff (no crash); the diff view shows an empty state.
- A record with an unknown IF `name`: skipped (returns `None`), run continues.
- A malformed JSON line: surfaced through stream health (reuse 009 behavior),
  not raised.
- IF events have no timestamp: the adapter synthesizes a deterministic,
  monotonic timestamp from the record `sequence` so replays stay deterministic.
- The summary payload shape varies by IF subcommand: the adapter maps the
  known top-level metrics it recognizes and ignores the rest (no crash on
  missing keys).
- Assembly items carry their id in `case_id` (IF quirk): the adapter reads the
  id from `work_item_id` when present, else `case_id`.

## Requirements *(mandatory)*

### Functional Requirements

**Pure normalizer**

- **FR-001**: The system MUST provide a pure, engine-free `adapt_record(record,
  *, run_id)` that maps an IF run-trace record (wrapper or inner
  `{sequence,name,payload}`) or a `summary` record to a canonical `Event`, or
  returns `None` for an unknown/ignored record.
- **FR-002**: The mapping MUST follow the table above (cases→tasks, assembly
  items→work items, file_diff→diff_ready, matrix lifecycle→run lifecycle,
  summary→evidence_ready).
- **FR-003**: The adapter MUST synthesize a valid envelope for every mapped
  event: stable `event_id` (from `sequence`), the caller's `run_id`, a
  deterministic monotonic `timestamp` (from `sequence`), and the correct
  `scope` (task_id / work_item_id).
- **FR-004**: The adapter MUST tolerate missing/empty `diff` and missing summary
  keys without raising.

**Source + CLI wiring**

- **FR-005**: The system MUST provide an `IntentForgeSource` (an `EventSource`)
  that reads IF ndjson from a file/line-iterable (replay) or a spawned
  `intentforge` subprocess (live) and yields adapted canonical envelopes,
  including the trailing summary.
- **FR-006**: `intui watch` MUST accept `--adapter intentforge` so a captured IF
  file or a `-- intentforge …` subprocess renders through the adapter.
- **FR-007**: Malformed lines and unknown records MUST be handled gracefully
  (health/skip), never crashing the runner (reuse feature 009 behavior).

**Public-safety & contract**

- **FR-008**: The adapter MUST NOT weaken public-safety: it forwards IF's
  already-redacted diffs and the console's default-on redaction remains
  (Principle VI). It MUST NOT introduce abs paths/secrets into payloads.
- **FR-009**: Adapter output MUST validate against `KNOWN_EVENT_TYPES` with no
  envelope errors (it emits only canonical types).

**Cross-cutting**

- **FR-010**: `adapt_record` and `IntentForgeSource` MUST be engine-free
  (no Textual import; layering guard) and headlessly testable (Principle VII).
- **FR-011**: The feature MUST ship a runnable example demonstrating an IF run
  rendered through the adapter (Principle VIII), using a committed IF-shaped
  fixture.

### Key Entities

- **adapt_record**: the pure IF-record → canonical-`Event` normalizer.
- **IntentForgeSource**: an `EventSource` that adapts an IF ndjson stream
  (file/line-iterable or subprocess) into canonical envelopes.
- **`--adapter intentforge`**: the `intui watch` switch selecting the adapter.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A captured IF stream renders a full console with **one command**
  (`intui watch --adapter intentforge <file>`) and **zero IF-specific code in
  the console/kit** (verified headlessly + an example).
- **SC-002**: All IF events in the mapping table reduce into the correct
  canonical slice (verified per-event headlessly).
- **SC-003**: A live IF-shaped subprocess is adapted into the console as events
  arrive; exit is reflected as stream end (verified).
- **SC-004**: The trailing summary becomes an evidence artifact (verified).
- **SC-005**: Adapter output has zero envelope errors against `KNOWN_EVENT_TYPES`
  (verified with the validator).
- **SC-006**: Missing/empty diff, unknown names, and malformed lines never crash
  (verified).

## Assumptions

- The IF event shapes are as verified in the IF repo on 2026-06-14
  (`run_trace.py`, `assembly_executor.py`, `assembly_benchmark.py`,
  `file_diff.py`, `cli.py`): records are `{sequence,name,payload}`, payload keys
  are the public-safe set, the stream wraps each as
  `{"type":"run_trace_event","event":…}` and ends with `{"type":"summary",…}`.
- The console/kit/contract are unchanged — this feature only adds the adapter
  layer and the CLI switch. Any new canonical *behavior* would be a kit change,
  out of scope here.
- The adapter targets the assembly-benchmark stream (the one that emits
  `--event-stream ndjson` today); other IF subcommands that emit the same record
  shape are covered for free.
- We do not vendor or import IntentForge; the adapter only understands its
  on-the-wire JSON shape (loose coupling). The IF repo is read-only reference.
- Live watching spawns `intentforge` (the user's installed CLI); the runner does
  not manage IF installation.
