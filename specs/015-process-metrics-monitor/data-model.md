# Data Model: Process Metrics Monitor

**Feature**: `015-process-metrics-monitor` | **Date**: 2026-06-14

## Events (canonical vocabulary additions)

| `type` | scope | payload | envelope status | meaning |
|---|---|---|---|---|
| `process_started` | — | `label` (sanitized command name) | — | a monitored process began |
| `metric_sample` | — | `cpu_percent` (float), `rss_bytes` (int), `elapsed_ms` (int) | — | one usage sample |
| `process_exited` | — | `exit_code` (int), `duration_ms` (int) | `passed`/`failed` | the process ended |

`METRICS_EVENT_TYPES = frozenset({"process_started","metric_sample",
"process_exited"})`, unioned into `KNOWN_EVENT_TYPES`.

## `metrics` slice (engine-free)

```text
MetricsSample(cpu_percent: float, rss_bytes: int, elapsed_ms: int)
MetricsState(
    label: str = "",
    status: str = "idle",          # idle/running/passed/failed
    cpu_percent: float = 0.0,      # latest
    rss_bytes: int = 0,            # latest
    peak_rss_bytes: int = 0,
    elapsed_ms: int = 0,           # latest sample / final duration
    exit_code: int | None = None,
    samples: tuple[MetricsSample, ...] = (),   # bounded ring (last N, default 60)
)
metrics_slice(window: int = 60) -> (reducer, MetricsState)
```

Reducer:
- `process_started` → status `running`, label set, history cleared.
- `metric_sample` → update latest cpu/rss/elapsed, bump `peak_rss_bytes`, append
  to `samples` (trim to `window`).
- `process_exited` → status `passed` (exit 0 / envelope status) else `failed`;
  set `exit_code`, `elapsed_ms` = `duration_ms`.

## Tree view model + selector

```text
MetricsView(
    label: str, status: str, glyph: str, status_label: str,
    cpu_percent: float, rss_human: str, peak_human: str, duration_human: str,
    cpu_spark: str, mem_spark: str, sample_count: int, present: bool,
)
metrics_view(slice_name="metrics", *, public_safe=True) -> Selector[MetricsView]
```

- `glyph`/`status_label` from `status_presentation` (running→active).
- `rss_human`/`peak_human` via `human_bytes` (e.g. `48.2 MB`); `duration_human`
  e.g. `1.2s` / `01:05`.
- `cpu_spark`/`mem_spark` via `sparkline(values)` over the sample window
  (`▁▂▃▄▅▆▇█`, scaled to max).
- `label` redacted when `public_safe` (default).
- `present` False when no process seen (empty state).

Pure helpers (unit-tested): `sparkline(values) -> str`, `human_bytes(n) -> str`.

## `ProcessMonitorSource` (engine-free, `intui.events.process`)

```text
ProcessMonitorSource(cmd: Sequence[str], *, interval: float = 1.0,
                     run_id: str = "process")  -> EventSource
```

- Lazily loads `psutil` (clear `RuntimeError` naming `in-tui-tion[metrics]` if
  missing). Spawns `cmd` (no shell; std streams to DEVNULL).
- Emits `process_started` (label = basename of `cmd[0]`), then a `metric_sample`
  per `interval` (cpu_percent/rss_bytes/elapsed_ms), then `process_exited`
  (exit_code, duration_ms; status passed/failed). Yields raw envelope mappings.
- Non-blocking via a single `proc.wait()` waiter + `asyncio.wait(timeout=interval)`;
  a vanished process / spawn failure ends the stream cleanly.

## `MetricsPanel` widget (rendering layer)

`MetricsPanel(BoundContainer)` over `metrics_view`:
- Shows `glyph status_label · label · duration · CPU x% · mem cur/peak` and the
  CPU/mem sparklines; empty state when `present` is False. Pure projection.

## Producer SDK

```text
RunRecorder.metric_sample(*, cpu_percent=0.0, rss_bytes=0, elapsed_ms=0) -> Event
```

Thin wrapper over `emit("metric_sample", ...)` for tools emitting their own
metrics (no `psutil`). (`process_started`/`process_exited` remain available via
the generic `emit`.)

## Console integration

- `ConsoleApp`: `"metrics"` added to `VIEWS`, a `metrics` slice in
  `build_console`, a `MetricsPanel` pane, and `Command("view_metrics","Metrics",
  select_view_intent("metrics"), key="m")`.
- `intui watch --metrics -- <cmd>` builds `ProcessMonitorSource(cmd)` instead of
  `SubprocessSource`.

## What does NOT change

- Envelope, store, health, snapshots, existing slices/widgets/views. Additive:
  3 event types, a slice + selector + helpers, a source, a widget, a console
  view, a CLI flag, an SDK helper, and the optional `metrics` extra.
