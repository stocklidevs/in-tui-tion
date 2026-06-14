# Implementation Plan: Process Metrics Monitor

**Branch**: `015-process-metrics-monitor` | **Date**: 2026-06-14 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/015-process-metrics-monitor/spec.md`

## Summary

"Run it and watch it work," done the event-sourced way:

1. **Metric events + state (engine-free, `intui.kit.state.metrics`)**:
   `METRICS_EVENT_TYPES = {process_started, metric_sample, process_exited}` →
   `metrics_slice()` reducing into `MetricsState` (current cpu/rss, peak rss,
   elapsed/duration, status, label, bounded sample history) + `metrics_view()`
   selector (human-readable memory, status presentation, CPU/mem sparkline
   strings, label redacted by default). Unioned into `KNOWN_EVENT_TYPES`.
2. **`ProcessMonitorSource` (engine-free, `intui.events.process`)**: spawns a
   command (`asyncio.create_subprocess_exec`), samples it every `interval` via
   `psutil`, yields the metric events, ends with `process_exited`. `psutil` is an
   **optional extra**; a clear error names `in-tui-tion[metrics]` if absent.
3. **`MetricsPanel` widget (`intui.kit.metrics_panel`)**: status + duration +
   CPU % + current/peak memory + sparkline, derived from the snapshot.
4. **Integration**: a "metrics" view (key `m`) in `ConsoleApp` + a `metrics`
   slice; `intui watch --metrics -- <cmd>` uses `ProcessMonitorSource`. Emit SDK
   gains `metric_sample(...)`. An example monitors a short command.

Decisions in [research.md](research.md); shapes in [data-model.md](data-model.md);
surface in [contracts/contract-api.md](contracts/contract-api.md).

## Technical Context

**Language/Version**: Python 3.11–3.13 (unchanged).

**Primary Dependencies**: Textual 6.x (the panel). **New optional dep**: `psutil`
(extra `metrics`), also added to the dev group so tests exercise it. Source uses
stdlib `asyncio`; sparkline/format are stdlib.

**Storage**: ndjson (metric events recordable/replayable like any others).

**Testing**: pytest headless for the slice (samples → current/peak/status/spark),
the selector (view + sparkline + label redaction), the `metric_sample` SDK
helper, and `ProcessMonitorSource` (spawn `sys.executable -c` a brief sleeper →
lifecycle + status; a `psutil`-missing path via monkeypatched import); Pilot for
the `MetricsPanel` + the console metrics view; a CLI test for `--metrics`.

**Target Platform**: Windows/macOS/Linux/WSL (`psutil` is cross-platform;
`create_subprocess_exec`, no shell).

**Project Type**: library + examples gallery (unchanged).

**Performance Goals**: sampling is async + non-blocking; the sample history is a
bounded ring (fixed window), so memory stays O(window).

**Constraints**: slice/selector/source/SDK engine-free (layering guard; `psutil`
is not Textual); public-safe label by default; replayable (metric events are
ordinary envelopes). `psutil` stays optional — the base import never requires it.

**Scale/Scope**: metrics state + selector + source + panel + console view + CLI
flag + SDK helper + example + the optional extra. Out of scope: summing child
processes, merging the monitor with the program's stdout/event stream, per-core
or disk/net counters.

## Constitution Check

| # | Principle | Status | Notes |
|---|-----------|--------|-------|
| I | Structured State | ✅ PASS | Metrics derive from the slice/snapshot; the panel is pure projection. |
| II | Layered Architecture | ✅ PASS | Slice/selector/source/SDK engine-free; only `MetricsPanel`/`ConsoleApp` import Textual. |
| III | Actions Are Intents | ✅ PASS (n/a) | Read-only monitoring; the user chose the command (not a sandbox). |
| IV | Keyboard-First | ✅ PASS | Metrics view reachable by key/command. |
| V | Meaningful Motion | ✅ PASS | Live-updating usage + status glyph (non-color identity). |
| VI | Public-Safe | ✅ PASS | Command label sanitized + redacted by default; metrics are numbers. |
| VII | Test-First, Replayable | ✅ PASS | Slice/selector/source headless test-first; metric events replay deterministically. |
| VIII | Example-Driven | ✅ PASS | An example monitors a command; console metrics view ships it. |
| — | New deps justified | ✅ PASS | `psutil` is the cross-platform way to read CPU/RSS; isolated as an optional extra. |

**Post-Phase-1 re-check (2026-06-14)**: `psutil` is optional (extra + dev) and
imported lazily inside the source; base import + layering unaffected. GATE: PASS.

## Project Structure

```text
src/intui/kit/state/
├── metrics.py      # NEW — METRICS_EVENT_TYPES, MetricsState, metrics_slice(),
│                   #   MetricsView, metrics_view(), sparkline + human-bytes helpers
└── __init__.py     # export metrics names; union into KNOWN_EVENT_TYPES

src/intui/events/
├── process.py      # NEW — ProcessMonitorSource (+ lazy psutil loader/error)
└── __init__.py     # export ProcessMonitorSource

src/intui/kit/
├── metrics_panel.py  # NEW — MetricsPanel(BoundContainer)
└── __init__.py       # lazy-export MetricsPanel

src/intui/emit.py    # + metric_sample(...) helper
src/intui/console/app.py  # "metrics" view (key m) + metrics slice
src/intui/console/cli.py  # --metrics flag -> ProcessMonitorSource for the `-- cmd` form
pyproject.toml       # [project.optional-dependencies] metrics = ["psutil>=5"]; dev += psutil

examples/process_monitor/  # __init__/__main__/run + README (monitor a short command)

tests/
├── unit/
│   ├── test_metrics.py          # slice + selector + sparkline/human-bytes + SDK helper
│   ├── test_process_source.py   # ProcessMonitorSource spawn/sample/exit + psutil-missing
│   └── test_console_cli.py      # (extend) --metrics wiring
├── snapshot/
│   └── test_metrics_panel.py    # Pilot: panel shows status/duration/cpu/mem/spark
└── integration/
    └── test_console_app.py      # (extend) metrics view reachable + shows metrics
```

**Structure Decision**: metrics join the engine-free kit slices; the source lives
in `intui.events` beside the other sources (lazy `psutil`); the only
rendering-layer additions are `MetricsPanel` and the console view/flag.

## Complexity Tracking

No constitutional violations — table intentionally empty.
