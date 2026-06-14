# Research & Decisions: Process Metrics Monitor

**Feature**: `015-process-metrics-monitor` | **Date**: 2026-06-14

## D1 — Metrics are an event stream (not a special live widget)

**Decision**: A monitored process emits `process_started` / `metric_sample` /
`process_exited` events that reduce into a `metrics` slice rendered by a panel —
the same pipeline as everything else.

**Why**: Keeps metrics replayable, recordable, and public-safe by construction
(Principle I/VI/VII); a recorded run's CPU/mem can be scrubbed later like any
state. It also means a producer can emit its own metrics without `psutil`.

**Alternatives rejected**: a widget that polls `psutil` directly — breaks the
state-derived model, isn't replayable, couples rendering to live IO.

## D2 — `psutil` as an optional extra, lazily imported

**Decision**: `psutil` is `in-tui-tion[metrics]`; `ProcessMonitorSource` imports
it lazily and raises a clear `RuntimeError` naming the extra if it is missing.
Added to the dev group so the suite exercises real sampling.

**Why**: Cross-platform CPU/RSS essentially requires `psutil`, but the base
install should stay dependency-light (only Textual). Lazy import keeps
`intui.events` importable without `psutil` and the layering guard green.

**Alternatives rejected**: hand-rolled per-OS `/proc`/WMI sampling — fragile and
large; making `psutil` a hard dep — weight on every install for an optional
capability.

## D3 — Curated metric set + bounded history

**Decision**: Track status, duration, CPU %, RSS (current + peak), and a bounded
recent-sample window (default 60) for sparklines. No per-core/disk/net counters.

**Why**: Answers "running and healthy?" without dashboard noise; the bounded ring
keeps memory O(window) for long runs. Peak RSS is the one derived value worth
keeping (spotting a spike after the fact).

**Alternatives rejected**: dump every psutil counter — noise + unbounded growth;
no history — loses the sparkline that makes a trend legible.

## D4 — Sample loop via a single `proc.wait()` task + `asyncio.wait` timeout

**Decision**: Spawn with `create_subprocess_exec` (no shell, stdout/stderr to
DEVNULL); create one `waiter = ensure_future(proc.wait())`; loop
`await asyncio.wait({waiter}, timeout=interval)` — if the waiter finished, stop;
else take a sample. Prime `cpu_percent()` once before the loop (psutil's first
call returns 0, subsequent calls are deltas).

**Why**: Non-blocking and integrates with Textual's loop (FR-006); one waiter
avoids re-awaiting `proc.wait()` repeatedly; the timeout drives the cadence
cleanly. A process that vanishes between poll and read (`psutil.NoSuchProcess`)
ends the loop gracefully.

**Alternatives rejected**: a reader thread — unnecessary given the event loop;
busy-polling `proc.returncode` — it doesn't update without awaiting `wait()`.

## D5 — `exit_code → status` (0 = passed, else failed)

**Decision**: `process_exited` sets the envelope `status` to `passed` for exit 0,
else `failed`; payload carries `exit_code` and `duration_ms`.

**Why**: Maps onto the same status presentation (glyph + label) the rest of the
kit uses; "did my code succeed?" is the headline outcome.

**Alternatives rejected**: signal-aware nuance (timed-out vs crashed) — deferred;
exit-code sign is enough for v1.

## D6 — Sparkline + human bytes are pure helpers in the selector

**Decision**: `metrics_view()` produces the sparkline strings (`▁▂▃▄▅▆▇█`
scaled to the window max) and human-readable memory (`48.2 MB`) — pure functions,
unit-tested headlessly; the widget just displays them.

**Why**: Keeps formatting logic testable without a terminal (Principle VII) and
the widget thin. Non-color glyphs/labels keep status legible without color
(Principle IV/V).

**Alternatives rejected**: render the sparkline in the widget — pushes logic into
the rendering layer and out of test reach.

## D7 — Monitor source emits metrics only; CLI `--metrics` switches the source

**Decision**: `ProcessMonitorSource` emits **only** metric events. `intui watch
--metrics -- <cmd>` uses it instead of `SubprocessSource` (which reads the
program's stdout as events). Watching a program's console *and* its metrics
simultaneously (merging two sources) is deferred.

**Why**: One source → one concern keeps the design clean and avoids a source-merge
abstraction this milestone doesn't need. The flag makes the choice explicit and
discoverable.

**Alternatives rejected**: a source that both reads stdout and samples — conflates
two streams and complicates ordering/backpressure; defer until there's demand.

## D8 — Command label sanitized + redacted

**Decision**: `process_started` carries a `label` = basename of `argv[0]`; the
selector redacts the label by default (public_safe).

**Why**: A full command line can leak absolute paths/secrets; a basename is
enough to identify the run, and default redaction is the safety net (Principle
VI).

**Alternatives rejected**: emit the full argv — leaks host paths; no label —
the panel can't say *what* is running.

## Open questions / deferred

- **Child processes**: v1 measures the spawned process; summing the tree is
  deferred (psutil supports `children(recursive=True)` when wanted).
- **Source merging** (program events + metrics together) — future.
- **More counters** (threads, fds, disk/net, per-core) — add if asked.
