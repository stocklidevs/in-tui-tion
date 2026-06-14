# API Contract: Process Metrics Monitor

**Feature**: `015-process-metrics-monitor` | **Date**: 2026-06-14

New public surface and guarantees tests pin.

## Events

- `process_started` (`label`), `metric_sample` (`cpu_percent`, `rss_bytes`,
  `elapsed_ms`), `process_exited` (`exit_code`, `duration_ms`; envelope status
  passed/failed) are canonical; `METRICS_EVENT_TYPES ⊆ KNOWN_EVENT_TYPES`.

## `intui.kit.state` — metrics model (engine-free)

```python
metrics_slice(window=60) -> tuple[Reducer, MetricsState]
metrics_view(slice_name="metrics", *, public_safe=True) -> Selector[MetricsView]
sparkline(values) -> str        # ▁▂▃▄▅▆▇█ scaled to max ("" for empty)
human_bytes(n) -> str           # e.g. "48.2 MB"
MetricsState, MetricsSample, MetricsView, METRICS_EVENT_TYPES
```

Guarantees:
- The reducer tracks latest cpu/rss/elapsed, peak rss, status (running →
  passed/failed on exit), exit code, and a history bounded to `window`.
- `metrics_view` exposes human-readable memory/duration, status glyph+label, and
  CPU/mem sparkline strings; `label` redacted when `public_safe` (default);
  `present` False with no process.

## `intui.events` — monitor source (engine-free)

```python
from intui.events import ProcessMonitorSource
ProcessMonitorSource(cmd, *, interval=1.0, run_id="process") -> EventSource
```

Guarantees:
- Spawns `cmd` (no shell), emits `process_started` → periodic `metric_sample` →
  `process_exited`; status passed for exit 0 else failed.
- Missing `psutil` raises a clear error naming `in-tui-tion[metrics]`.
- Sampling is non-blocking; a vanished process / spawn failure ends cleanly.
- Satisfies the existing `EventSource` Protocol (works with `Store.run`/`watch`).

## `intui.kit` — widget

```python
from intui.kit import MetricsPanel
MetricsPanel(metrics_view(...), ...)
```

Guarantees: renders status, duration, CPU %, current + peak memory, and a
sparkline from the snapshot; empty state when no process.

## `intui.emit` — SDK helper

```python
rec.metric_sample(*, cpu_percent=0.0, rss_bytes=0, elapsed_ms=0) -> Event
```

Guarantees: a valid `metric_sample` envelope reducing into the metrics slice.

## Console integration

- `ConsoleApp` exposes a `metrics` view by key `m`; `build_console` wires a
  `metrics` slice.
- `intui watch --metrics -- <cmd>` watches the command's resources
  (`ProcessMonitorSource`); without `--metrics`, `-- <cmd>` reads stdout events
  as before.

## Backward compatibility

- Purely additive: new event types, slice/selector/source/widget, a console view
  + CLI flag, an SDK helper, and an **optional** `metrics` extra. No existing
  signature changes; base install adds no required dependency.
