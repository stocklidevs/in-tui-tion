# process_monitor

Watch a command's **CPU and memory** live — feature 015. Spawns a short Python
workload and renders its status, duration, CPU %, memory (current + peak), and a
usage sparkline.

## Run it

```sh
pip install "intui[metrics]"      # adds psutil
uv run python -m examples.process_monitor
```

Press `m` for the metrics view.

## Or via the CLI

```sh
intui watch --metrics -- python build.py
```

## What's happening

`ProcessMonitorSource` spawns the command and samples it on an interval with
`psutil`, emitting `process_started` → `metric_sample` → `process_exited`. Those
reduce into the `metrics` slice and render in the `MetricsPanel` — the same
event-sourced path as everything else, so the run is replayable and the command
label is public-safe by default.
