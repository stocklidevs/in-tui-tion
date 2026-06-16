# Research & Decisions: pytest Plugin

**Feature**: `019-pytest-plugin` | **Date**: 2026-06-14

## D1 — Ship in intui via the `pytest11` entry point; inert unless `--intui`

**Decision**: The plugin lives inside intui (`intui.pytest_plugin`) and is
auto-discovered through the `pytest11` entry point. It only registers a
`--intui[=PATH]` option and does nothing else unless that option is given.

**Why**: One install (`pip install intui`) gives both the console and the pytest
integration — lowest friction for the adoption demo. Auto-load is safe because
the plugin is a no-op without the flag (no output, no files, no behavior change),
which is the standard, trusted pattern for bundled pytest plugins.

**Alternatives rejected**: a separate `pytest-intui` distribution — more to
install/maintain for v1 (a possible future split). A non-entry-point plugin
requiring `-p intui.pytest_plugin` — extra friction every run.

## D2 — Emit via `run_recorder` (no new vocabulary)

**Decision**: The plugin produces canonical events through the Producer SDK
(`run_recorder`) — `run_started`, `work_item_*`, `message_added`,
`evidence_ready`, `run_completed`. No pytest-specific event types.

**Why**: The whole point is that pytest becomes an ordinary producer — the output
is plain canonical ndjson that `intui watch`/`--follow`/scrub/record consume with
no adapter. Reusing the SDK means zero new serialization and automatic
consistency with the contract.

**Alternatives rejected**: pytest-specific events + a pytest adapter — needless
indirection when the SDK already covers the mapping.

## D3 — Module = task, test = work item (parent inference)

**Decision**: Each test is a `work_item` scoped to its module file
(`task_id = location filename`, `work_item_id = node id`, title = test name).
Modules become tasks via the kit's parent-node inference (011/013) — the plugin
emits **no** task lifecycle events.

**Why**: Gives a natural two-level tree (module → tests) for free, and avoids
guessing module start/finish boundaries. Node ids make work items unique
(parametrized cases included).

**Alternatives rejected**: flat tests-as-tasks — loses the module grouping;
explicit task_started/completed per module — needs boundary tracking the
inference already handles.

## D4 — Outcome from accumulated reports; emit on logstart/logfinish

**Decision**: `pytest_runtest_logstart` emits `work_item_started`;
`pytest_runtest_logreport` accumulates the test's outcome across setup/call/
teardown (failed if any phase failed; skipped if skipped; else passed);
`pytest_runtest_logfinish` emits `work_item_completed` with that outcome (+ a
`message_added` on failure).

**Why**: `logstart`/`logfinish` bracket each test cleanly (one started + one
completed), while the outcome must be derived from the phase reports (a setup or
teardown error is still a failure). This is the robust, well-trodden pattern.

**Alternatives rejected**: emit only on the `call` report — misses setup-skips
and teardown errors and can double/skip events.

## D5 — Isolated state via a registered reporter object

**Decision**: `pytest_configure` creates an `_IntuiReporter(recorder)` and
`config.pluginmanager.register(...)` it; all per-run state (started set, outcome
map, counters, start time) lives on that object.

**Why**: Avoids module-global state (cleaner, no leakage between in-process runs)
and lets pytest dispatch the hook methods normally.

**Alternatives rejected**: module-level globals — fragile across runs/tests.

## D6 — Session end → evidence + run status; write failures warn

**Decision**: `pytest_sessionfinish` emits `evidence_ready` with
passed/failed/skipped/total + duration, then `run_completed` (status `failed` if
any failures or non-zero exit, else `passed`), and closes the recorder. If the
recorder can't be opened (bad `--intui` path), `pytest_configure` warns and
disables the plugin rather than crashing the run.

**Why**: The summary is the headline outcome; mapping it to evidence + run status
drives the panel and the activity strip. A test run must never fail because the
*observability* sink is misconfigured (FR-006).

**Alternatives rejected**: raise on a bad path — breaks the user's test run for a
non-essential feature.

## Open questions / deferred

- **xdist / parallel**: out of scope v1 (state is per-process; document).
- **Full traceback capture** (as a diff/evidence blob): deferred — a concise
  failure message keeps the stream public-safe and small.
- **Adapter registry + more producers** (logfmt/JSON logs, OpenTelemetry): the
  next steps of the broaden-adoption arc.
