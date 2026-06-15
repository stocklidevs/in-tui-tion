# Quickstart: Process Metrics Monitor

Run a command and watch its resources — status, duration, CPU, memory, sparkline.

## Install the extra

```sh
pip install "intui[metrics]"     # adds psutil
```

## Watch a command live

```sh
intui watch --metrics -- python build.py
```

Press `m` for the metrics view. You'll see it run and then finish:

```
» running · build.py · 2.4s · CPU 38% · mem 51.2 MB / 63.0 MB
cpu ▁▂▄▆█▆▅▃   mem ▂▃▄▅▆▇▇█
```

## From Python

```python
from intui.console import watch
from intui.events import ProcessMonitorSource

watch(ProcessMonitorSource(["python", "build.py"], interval=0.5))
```

## Emit your own metrics (no psutil)

A tool can report metrics itself via the SDK:

```python
from intui import run_recorder
rec = run_recorder()
rec.metric_sample(cpu_percent=42.0, rss_bytes=53_400_000, elapsed_ms=1200)
```

## Notes

- `psutil` is an **optional extra**; without it the monitor raises a clear
  "install intui[metrics]" error.
- v1 measures the spawned process itself (summing child processes is deferred).
- The command **label** is sanitized to a basename and redacted by default — no
  host paths leak (Principle VI).
- Metric events are ordinary stream events: record them and replay the run's
  resource usage like anything else.
- This source watches **resources**; to watch a program's own console/events,
  use the default `intui watch -- <cmd>` (stdout events). Watching both at once
  is a future feature.
