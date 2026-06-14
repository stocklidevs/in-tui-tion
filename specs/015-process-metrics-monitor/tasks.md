# Tasks: Process Metrics Monitor

**Feature**: `015-process-metrics-monitor` | **Input**: plan.md, research.md,
data-model.md, contracts/contract-api.md

Test-first throughout (Principle VII). `[P]` = parallelizable. Gate after each
phase: `uv run pytest && uv run ruff check && uv run mypy`.

## Phase 1 — Metrics state + selector (engine-free)

- [ ] **T001** [P] Write `tests/unit/test_metrics.py`: `process_started` →
      running + label; `metric_sample` updates latest cpu/rss/elapsed, bumps peak,
      appends to bounded history (trims to window); `process_exited` → passed
      (exit 0 / status) or failed + exit_code + duration; `metrics_view` exposes
      human memory/duration, status glyph+label, cpu/mem sparklines, redacted
      label (public_safe) + raw when off, `present` flag; `sparkline`/`human_bytes`
      pure helpers; `METRICS_EVENT_TYPES ⊆ KNOWN_EVENT_TYPES`.
- [ ] **T002** Implement `src/intui/kit/state/metrics.py` (events const, models,
      `metrics_slice`, `metrics_view`, `sparkline`, `human_bytes`).
- [ ] **T003** Export metrics names from `src/intui/kit/state/__init__.py`
      (+ `__all__`); union into `KNOWN_EVENT_TYPES`; update
      `tests/unit/test_vocabulary.py` module-set list. Make T001 pass.

## Phase 2 — ProcessMonitorSource

- [ ] **T004** [P] Write `tests/unit/test_process_source.py`: spawn
      `sys.executable -c "import time;time.sleep(0.3)"` with a small interval via
      `ProcessMonitorSource`; drive a store; assert `process_started`,
      `process_exited` present, status passed (exit 0), ≥0 samples; a non-zero
      exit → failed; a `psutil`-missing path (monkeypatch import) raises a clear
      error naming the extra.
- [ ] **T005** Implement `src/intui/events/process.py` (`ProcessMonitorSource`,
      lazy `_load_psutil()` with clear error, sample loop) and export from
      `src/intui/events/__init__.py`. Make T004 pass.
- [ ] **T006** Add `psutil` as an optional extra
      (`[project.optional-dependencies] metrics`) and to the dev group in
      `pyproject.toml`; `uv sync`.

## Phase 3 — MetricsPanel widget (Pilot)

- [ ] **T007** [P] Write `tests/snapshot/test_metrics_panel.py` (Pilot): reduce
      metric events, mount `MetricsPanel`, assert it shows status/duration/CPU/
      memory and a sparkline; empty state with no process.
- [ ] **T008** Implement `src/intui/kit/metrics_panel.py`
      (`MetricsPanel(BoundContainer)`) + lazy-export from `intui/kit/__init__.py`;
      add TID251 per-file-ignore. Make T007 pass.

## Phase 4 — SDK helper + console + CLI

- [ ] **T009** [P] Extend `tests/unit/test_emit.py`: `rec.metric_sample(...)`
      emits a valid `metric_sample` reducing into the metrics slice.
- [ ] **T010** Add `metric_sample(...)` to `src/intui/emit.py`.
- [ ] **T011** Wire the console: `"metrics"` in `VIEWS`, a `metrics` slice in
      `build_console`, a `MetricsPanel` pane, and `Command("view_metrics",
      "Metrics", select_view_intent("metrics"), key="m")` in
      `src/intui/console/app.py`.
- [ ] **T012** Add `--metrics` to `src/intui/console/cli.py` (the `-- cmd` form
      uses `ProcessMonitorSource`); extend `tests/unit/test_console_cli.py` and
      `tests/integration/test_console_app.py` (metrics view reachable; a metric
      stream shows the panel).

## Phase 5 — Example, docs, gate, verify, merge

- [ ] **T013** [P] Add `examples/process_monitor/{__init__,__main__,run}.py` +
      `README.md`: monitor a short Python command (watchable live).
- [ ] **T014** [P] Docs: add the metric events to
      `docs/event-stream-contract.md`; a metrics line in `docs/quickstart.md`;
      README `[metrics]` extra + `--metrics` mention; link the feature quickstart.
- [ ] **T015** Confirm layering: metrics slice/selector + `ProcessMonitorSource`
      + SDK helper stay engine-free (`test_layering.py`).
- [ ] **T016** Full gate: `uv run pytest && uv run ruff check && uv run mypy`;
      bump `src/intui/__init__.py` `__version__` to `0.15.0`.
- [ ] **T017** Fresh-build verify: `uv build` + clean-install **with the extra**
      (`pip install <wheel>[metrics]`); spot-check `ProcessMonitorSource` reduces
      a short command and `from intui.kit import MetricsPanel` imports.
- [ ] **T018** Merge: `git merge --no-ff` `015-process-metrics-monitor` into
      `main`; update project memory (015 done; metrics monitor shipped).

## Dependencies

- T002 ← T001; T003 ← T002. T005 ← T004; T006 alongside T005. T008 ← T007 (+ T002).
- T010 ← T009. T011 ← T008+T002. T012 ← T005+T011.
- T013 ← T005; T014 after code; T015–T018 last, in order.

## Parallelizable

`[P]`: T001, T004, T007, T009, T013, T014 — distinct files.
