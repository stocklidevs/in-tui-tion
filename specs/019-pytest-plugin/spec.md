# Feature Specification: pytest Plugin (watch your tests)

**Feature Branch**: `019-pytest-plugin`

**Created**: 2026-06-14

**Status**: Draft

**Input**: Post-1.0 direction — *broaden adoption*. Turn a tool people already
run into an instant intui console. `pytest` is the most relatable Python on-ramp:
a plugin that emits the canonical event stream as the suite runs, so
`intui watch` renders tests as tasks/work items, failures in the conversation,
and a pass/fail summary as evidence — the flagship "point it at what you have"
demo and the start of the producer-adapter ecosystem.

## Overview

A built-in pytest plugin maps pytest's reporting hooks onto the canonical
vocabulary (via the Producer SDK) and writes them to a stream — opt-in with
`pytest --intui[=PATH]`. The plugin is **inert unless the flag is given** (it
just registers an option), adds **no runtime dependency** (it's only loaded by
pytest, which is obviously present then), and produces an ordinary canonical
`.jsonl` — so the whole existing toolchain applies: `intui watch run.jsonl`,
`--follow` it live in a second terminal, scrub it, record it.

Mapping (test module → task, test → work item):

| pytest | canonical |
|---|---|
| session start | `run_started` |
| a test starts | `work_item_started` (`task_id` = module path, `work_item_id` = node id) |
| a test passes/fails/skips | `work_item_completed` (status), failures also a `message_added` |
| session finish | `evidence_ready` (passed/failed/skipped/total/duration) + `run_completed` |

Modules appear as tasks via the kit's parent inference (013/011) — no separate
task events needed.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Watch a test run as a console (Priority: P1)

A developer runs `pytest --intui=run.jsonl`, then `intui watch run.jsonl` (or
`--follow` it live in another terminal). Tests show as work items grouped by
module, failures appear in the conversation, and the summary shows as evidence.

**Why this priority**: This is the whole feature and the adoption demo — zero
custom code, instant value on a universally-used tool.

**Independent Test**: Run a small synthetic suite (pass/fail/skip) under the
plugin with `--intui=<tmp>` (via pytest's `pytester`); read the stream back and
assert it reduces into the expected taskboard (modules→tasks, tests→work items
with correct statuses) and an evidence summary.

**Acceptance Scenarios**:

1. **Given** `pytest --intui=run.jsonl`, **When** the suite runs, **Then** the
   file contains canonical events: `run_started`, a `work_item_started`/
   `work_item_completed` pair per test (scoped to its module), and a final
   `evidence_ready` + `run_completed`.
2. **Given** that stream, **When** reduced, **Then** each module is a task and
   each test a work item under it with the right status (passed/failed/skipped).
3. **Given** a failing test, **When** reduced, **Then** the work item is `failed`
   and a conversation message names the failure.
4. **Given** the summary, **When** reduced, **Then** evidence shows
   passed/failed/skipped/total counts and the run status reflects failures.

---

### User Story 2 - Inert unless opted in (Priority: P1)

A developer who has intui + pytest installed but does **not** pass `--intui` sees
no change to their pytest run — no output, no files, no behavior change.

**Why this priority**: An auto-loaded plugin must never intrude; trust depends
on it doing nothing unless asked.

**Independent Test**: Run a suite **without** `--intui`; assert no stream file is
written and pytest behaves identically (the plugin only registered an option).

**Acceptance Scenarios**:

1. **Given** no `--intui`, **When** pytest runs, **Then** the plugin emits
   nothing and writes no files.
2. **Given** `--intui` with no value, **When** pytest runs, **Then** it writes to
   a sensible default path and reports where.

---

### User Story 3 - Live and replayable like any stream (Priority: P2)

The pytest stream is ordinary canonical ndjson, so it works with everything:
follow it live, replay it, scrub it, or record a copy.

**Why this priority**: Reusing the whole toolchain (no special pytest viewer) is
what makes this a *substrate* integration, not a one-off.

**Independent Test**: Point `intui watch --follow` at the file while a suite
writes it (or replay after); assert it renders without special handling.

**Acceptance Scenarios**:

1. **Given** the emitted file, **When** `intui watch <file>` runs, **Then** it
   renders with no adapter (canonical events).
2. **Given** `--follow`, **When** the suite appends, **Then** new tests appear
   live.

---

### Edge Cases

- A test that errors during setup/teardown (not just call): recorded as failed
  with a message; no crash in the plugin.
- A parametrized test: each parametrization is its own work item (distinct node
  id).
- An empty suite / collection error: `run_started` + a summary with zero counts;
  no crash.
- `xfail`/`xpass`: mapped to a sensible status (treated as passed/skipped-like;
  documented).
- Writing to an unwritable `--intui` path: a clear pytest-side error/warning, not
  a crash of the test run.
- The plugin must not alter pytest's own exit code or output.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Provide a pytest plugin (auto-discovered via the `pytest11` entry
  point) that adds a `--intui[=PATH]` option and is otherwise **inert** unless
  the option is given.
- **FR-002**: When enabled, the plugin MUST emit canonical events via the
  Producer SDK: `run_started` at session start; `work_item_started`/
  `work_item_completed` per test scoped to its module (so modules nest as tasks);
  a `message_added` for each failure; `evidence_ready` (passed/failed/skipped/
  total/duration) + `run_completed` (status reflecting failures) at the end.
- **FR-003**: The emitted file MUST be ordinary canonical ndjson that
  `intui watch`/`--follow`/replay/scrub consume with **no adapter**.
- **FR-004**: The plugin MUST add **no runtime dependency** to intui (loaded only
  within a pytest run) and MUST NOT change pytest's exit code, output, or
  behavior when not enabled.
- **FR-005**: Test status mapping MUST cover passed / failed / skipped (and
  xfail/xpass to a documented sensible status); errors in any phase are recorded,
  not raised.
- **FR-006**: A write failure MUST surface as a clear pytest-side warning/error,
  never crash the run.

### Key Entities

- **The pytest plugin** (`intui.pytest_plugin`): hooks → canonical events.
- **`--intui[=PATH]`**: the opt-in switch + destination.
- **Emitted stream**: canonical ndjson consumed by the existing runner.

## Success Criteria *(mandatory)*

- **SC-001**: `pytest --intui=run.jsonl` over a pass/fail/skip suite produces a
  canonical stream that reduces into modules-as-tasks, tests-as-work-items with
  correct statuses, failure messages, and an evidence summary (verified via
  `pytester`).
- **SC-002**: Without `--intui`, pytest behaves identically and writes nothing.
- **SC-003**: The emitted file renders via `intui watch` with no adapter.
- **SC-004**: No new runtime dependency; the plugin never changes pytest's exit
  code/output when not enabled.
- **SC-005**: The plugin code is engine-free (no Textual; uses pytest + the emit
  SDK) and headlessly testable.

## Assumptions

- The plugin ships **inside** intui (one install) with a `pytest11` entry point;
  it's safe to auto-load because it only adds an option and acts solely on
  `--intui`. (A separate `pytest-intui` distribution is a possible future split.)
- pytest is not a runtime dependency of intui; it's present whenever the plugin
  runs. Tests use pytest's `pytester` fixture.
- This is the first producer integration; a generic adapter registry + more
  adapters (logfmt/JSON logs, OpenTelemetry) are follow-ups, out of scope here.
- Live watching during a run is done in a **second terminal** (`--follow`) —
  pytest owns its own terminal; intui does not overlay it.
- Failure detail is summarized into a conversation message (concise), not a full
  diff/traceback dump.
