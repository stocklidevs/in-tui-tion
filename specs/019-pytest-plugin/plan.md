# Implementation Plan: pytest Plugin

**Branch**: `019-pytest-plugin` | **Date**: 2026-06-14 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/019-pytest-plugin/spec.md`

## Summary

A built-in pytest plugin that emits the canonical event stream as a suite runs:

- `src/intui/pytest_plugin.py` — `pytest_addoption` adds `--intui[=PATH]`
  (`nargs="?"`, default `None` = inert, const = a default filename).
  `pytest_configure` opens a `run_recorder(path)` and registers an
  `_IntuiReporter` plugin object (so all state is isolated, not module globals).
- `_IntuiReporter` hooks: `pytest_sessionstart` → `run_started`;
  `pytest_runtest_logstart` → `work_item_started` (task_id = module file,
  work_item_id = node id, title = test name); `pytest_runtest_logreport`
  accumulates the per-test outcome; `pytest_runtest_logfinish` →
  `work_item_completed` (+ a `message_added` on failure) and counters;
  `pytest_sessionfinish` → `evidence_ready` (passed/failed/skipped/total/
  duration) + `run_completed` (status from failures), then closes the recorder.
- `pyproject.toml`: `[project.entry-points.pytest11] intui =
  "intui.pytest_plugin"` (auto-discovered; inert unless `--intui`).

Modules nest as tasks via the kit's parent inference (011/013) — no task events
needed. Output is canonical ndjson → reuses `intui watch`/`--follow`/scrub with
no adapter. Decisions in [research.md](research.md); shapes in
[data-model.md](data-model.md).

## Technical Context

**Language/Version**: Python 3.11–3.13 (unchanged).

**Primary Dependencies**: none new at runtime. The plugin imports `pytest` (only
ever loaded inside a pytest run) + `intui.emit` (engine-free). `pytest` is
already a dev dependency.

**Storage**: canonical ndjson (the emitted stream).

**Testing**: pytest's `pytester` fixture (`runpytest_subprocess`) runs an
isolated suite (pass/fail/skip) with `--intui=<tmp>`; the test reads the stream
back and reduces it (taskboard + artifacts + run_status) to assert the mapping;
plus an inert-without-flag test and a reduce-through assertion.

**Target Platform**: unchanged.

**Project Type**: library + examples gallery (unchanged).

**Performance Goals**: negligible per-test overhead (a few flushed ndjson lines).

**Constraints**: plugin engine-free (no Textual); inert unless opted in; no
change to pytest's exit code/output; write failures warn, never crash; not loaded
by the `intui` root import. (xdist/parallel out of scope for v1.)

**Scale/Scope**: one plugin module + the entry point + an example + docs. Out of
scope: a generic adapter registry, more adapters (logfmt/OTel), xdist support,
full-traceback capture, a live in-pytest TUI overlay.

## Constitution Check

| # | Principle | Status | Notes |
|---|-----------|--------|-------|
| I | Structured State | ✅ PASS | Emits canonical events; all state still flows through the store/reducers downstream. |
| II | Layered Architecture | ✅ PASS | Plugin engine-free (pytest + emit SDK); not imported by the root. |
| III | Actions Are Intents | ✅ PASS (n/a) | Producer side; no UI intents. |
| IV | Keyboard-First | ✅ PASS (n/a) | The console (consume side) is unchanged. |
| V | Meaningful Motion | ✅ PASS | run lifecycle drives the activity strip when watched. |
| VI | Public-Safe | ✅ PASS | Output is canonical events; the console redacts on display as always. |
| VII | Test-First, Replayable | ✅ PASS | `pytester`-driven tests; emitted stream is replayable ndjson. |
| VIII | Example-Driven | ✅ PASS | Ships `examples/pytest_console` (a sample suite + how to watch it). |
| — | New deps justified | ✅ PASS | None — pytest only present when the plugin runs. |

**Post-Phase-1 re-check (2026-06-14)**: no new runtime deps; layering holds.
GATE: PASS — Complexity Tracking empty.

## Project Structure

```text
src/intui/pytest_plugin.py   # NEW — the plugin (addoption/configure + _IntuiReporter)
pyproject.toml               # + [project.entry-points.pytest11] intui = "intui.pytest_plugin"

examples/pytest_console/     # a sample test file + README (pytest --intui … ; intui watch …)

tests/unit/test_pytest_plugin.py  # pytester: emits canonical stream that reduces correctly;
                                  #   inert without --intui; failure -> message + failed status
```

**Structure Decision**: the plugin is a single engine-free module wired via the
`pytest11` entry point; it reuses `run_recorder` for all emission, so there's no
new serialization or event vocabulary — just a mapping from pytest hooks.

## Complexity Tracking

No constitutional violations — table intentionally empty.
