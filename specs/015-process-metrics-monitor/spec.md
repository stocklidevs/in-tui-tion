# Feature Specification: Process Metrics Monitor

**Feature Branch**: `015-process-metrics-monitor`

**Created**: 2026-06-14

**Status**: Draft

**Input**: From the workspace discussion — "run the generated code from within
in-TUI-tion and see resources/process metrics." Running is already possible
(`SubprocessSource`); this adds **resource monitoring**: spawn a command, sample
its CPU/memory live, and render status/duration/usage as events, the same
event-sourced way as everything else.

## Overview

A generic "run it and watch it work" capability: a `ProcessMonitorSource` spawns
a command, samples it on an interval (via `psutil`), and emits **metric events**
(`process_started`, `metric_sample`, `process_exited`). Those reduce into a
`metrics` slice and render in a `MetricsPanel` — status, wall-clock duration,
CPU %, memory (current + peak), and a CPU/memory sparkline. It is a first-class
TUI primitive (a process/resource monitor), not an IF special case, and it stays
in our model: metrics are just another event stream → state → widget, so it is
replayable and public-safe like the rest.

`psutil` is an **optional extra** (`pip install in-tui-tion[metrics]`); the
source raises a clear, actionable error if it is missing. The console gains a
"metrics" view and an `intui watch --metrics -- <cmd>` switch.

Which metrics matter (curated, not a dashboard): **exit status, duration, CPU %,
RSS memory (current + peak), and recent-history sparklines** — enough to answer
"is my code running, and is it healthy?" without noise.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Watch a command's resources live (Priority: P1)

A developer runs `intui watch --metrics -- python build.py` (or
`watch(ProcessMonitorSource([...]))`). The console shows the process running:
elapsed time climbing, CPU % and memory updating each sample, then the final
status (passed/failed) when it exits.

**Why this priority**: "run it and watch it work" is the headline capability and
the second half of the workspace+run vision.

**Independent Test**: Spawn a short-lived `sys.executable -c …` command through
`ProcessMonitorSource`; drive it into a store; assert `process_started`, ≥0
`metric_sample`s, and `process_exited` (status passed for exit 0) reduce into the
metrics slice.

**Acceptance Scenarios**:

1. **Given** `ProcessMonitorSource(cmd)`, **When** the command runs, **Then** it
   emits `process_started`, periodic `metric_sample`s (cpu/memory/elapsed), and a
   final `process_exited` with the exit status.
2. **Given** the samples, **When** reduced, **Then** the metrics slice tracks
   current CPU/memory, peak memory, elapsed time, and status.
3. **Given** the command exits non-zero, **When** reduced, **Then** the status is
   `failed`; exit 0 → `passed`.
4. **Given** `psutil` is not installed, **When** the source is driven, **Then** a
   clear error names the `in-tui-tion[metrics]` extra (no obscure ImportError).

---

### User Story 2 - See the metrics in the console (Priority: P1)

The metrics render in a panel: status with a non-color glyph, duration, CPU %,
memory (current + peak), and a sparkline of recent usage — reachable in the
zero-config console.

**Why this priority**: The numbers are only useful rendered; the panel is the
deliverable users see.

**Independent Test**: Reduce metric events into a store; render the `MetricsPanel`
via Pilot; assert it shows status/duration/CPU/memory and a sparkline; assert the
console "metrics" view is reachable by key.

**Acceptance Scenarios**:

1. **Given** metric events, **When** the `MetricsPanel` renders, **Then** it
   shows status, duration, CPU %, current + peak memory, and a usage sparkline.
2. **Given** the console, **When** the user selects the metrics view, **Then**
   the panel is shown; the view is keyboard-reachable.
3. **Given** memory values, **When** displayed, **Then** they are human-readable
   (e.g. `48.2 MB`).

---

### User Story 3 - Replayable + public-safe like everything else (Priority: P2)

Metric events recorded to a stream replay into the same panel; the command label
is public-safe.

**Why this priority**: Consistency with the rest of the system (replay, safety)
is what makes metrics first-class rather than a bolted-on widget.

**Independent Test**: Record metric events; replay via the runner; assert the
panel reconstructs; assert the command label is sanitized/redacted by default.

**Acceptance Scenarios**:

1. **Given** a recording of metric events, **When** replayed, **Then** the panel
   reconstructs the run's metrics deterministically.
2. **Given** a command label that could leak a path, **When** displayed, **Then**
   it is redacted by default (Principle VI).

---

### Edge Cases

- A command that exits immediately: `process_started` + `process_exited` with few
  or no samples — no crash; status reflects the exit code.
- A command that cannot start (not found): surfaced as a disconnect/clear error,
  never a traceback.
- A very short interval / very long run: sampling is non-blocking; the sparkline
  keeps a bounded recent window (no unbounded growth).
- The monitored process spawns children: v1 measures the spawned process itself
  (summing children is deferred); documented.
- `psutil` missing: a clear "install in-tui-tion[metrics]" error.
- A sample failing mid-run (process vanished between poll and read): handled; the
  run ends cleanly.

## Requirements *(mandatory)*

### Functional Requirements

**Metric events + state (engine-free)**

- **FR-001**: Define canonical metric event types — `process_started`,
  `metric_sample` (payload cpu_percent, rss_bytes, elapsed_ms), `process_exited`
  (payload exit_code, duration_ms; envelope status passed/failed) — and union
  `METRICS_EVENT_TYPES` into `KNOWN_EVENT_TYPES`.
- **FR-002**: Provide a `metrics` slice reducing those events into current
  CPU/memory, peak memory, elapsed/duration, status, a command label, and a
  bounded recent-sample history (for sparklines).
- **FR-003**: Provide a `metrics_view` selector exposing the current values
  (human-readable memory), status presentation (glyph + label), and CPU/memory
  sparkline strings; public-safe (label redacted) by default.

**Monitor source**

- **FR-004**: Provide a `ProcessMonitorSource(cmd, *, interval=…)` (an
  `EventSource`) that spawns the command, samples it on the interval via
  `psutil`, and yields the metric events, ending with `process_exited`.
- **FR-005**: `psutil` MUST be an optional extra; a missing `psutil` MUST raise a
  clear error naming `in-tui-tion[metrics]` (not a bare ImportError).
- **FR-006**: Sampling MUST be non-blocking and bounded (a fixed-size recent
  window); a vanished process or spawn failure MUST end the stream cleanly.

**Widget + integration**

- **FR-007**: Provide a `MetricsPanel` bound widget rendering status, duration,
  CPU %, current + peak memory, and a sparkline; derived entirely from the
  snapshot (Principle I).
- **FR-008**: The `ConsoleApp` MUST expose a "metrics" view (reachable by key/
  command); `intui watch` MUST accept `--metrics -- <cmd>` to watch a command's
  resources (using `ProcessMonitorSource`).
- **FR-009**: The Producer SDK SHOULD provide a `metric_sample(...)` helper so a
  tool can emit its own metrics without `psutil`.

**Cross-cutting**

- **FR-010**: The slice, selector, source, and SDK helper MUST be engine-free
  (layering guard) and headlessly testable; the panel via Pilot. A runnable
  example MUST demonstrate monitoring a command (Principle VIII).

### Key Entities

- **Metric events**: `process_started`, `metric_sample`, `process_exited`.
- **MetricsState / MetricsView**: reduced usage + status + bounded history +
  sparkline.
- **ProcessMonitorSource**: spawn + sample (psutil) → metric events.
- **MetricsPanel**: the status/usage/sparkline widget.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `ProcessMonitorSource` over a real short command reduces into a
  metrics slice with the correct lifecycle + status (verified headlessly).
- **SC-002**: The `MetricsPanel` shows status, duration, CPU %, current + peak
  memory (human-readable), and a sparkline (verified via Pilot).
- **SC-003**: `intui watch --metrics -- <cmd>` watches a command's resources;
  the console metrics view is keyboard-reachable.
- **SC-004**: Missing `psutil` yields a clear `in-tui-tion[metrics]` error.
- **SC-005**: Metric events replay deterministically into the same panel; the
  command label is redacted by default.
- **SC-006**: All non-widget pieces are engine-free (layering guard green).

## Assumptions

- `psutil` is the cross-platform way to read CPU/RSS; it is an optional extra so
  the base install stays dependency-light.
- v1 measures the spawned process itself; summing child processes is deferred.
- The monitor source emits **metrics only** (not the program's stdout/events);
  watching a program's console *and* its metrics simultaneously (source merging)
  is a separate future feature.
- The command label is sanitized to a basename and redacted on display; raw host
  paths are never shown.
- Curated metric set (status/duration/CPU/RSS/peak/sparkline) is intentional —
  more counters can come later if asked.
