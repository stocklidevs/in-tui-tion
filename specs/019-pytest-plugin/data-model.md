# Data Model: pytest Plugin

**Feature**: `019-pytest-plugin` | **Date**: 2026-06-14

No new event types or state shapes — the plugin maps pytest hooks onto the
existing canonical vocabulary via `run_recorder`.

## Option

```text
pytest --intui[=PATH]
```
- absent → `None` → plugin inert (only the option is registered).
- bare `--intui` → a default path (e.g. `intui-pytest.jsonl` in the rootdir).
- `--intui=PATH` → that path.

## Plugin (`intui.pytest_plugin`)

```text
pytest_addoption(parser)        # registers --intui (nargs="?", const=default, default=None)
pytest_configure(config)        # if option set: open run_recorder(path); register _IntuiReporter
                                #   on failure: warnings.warn(...) and do not register (inert)
```

`_IntuiReporter` (registered plugin object; holds the recorder + per-run state):

| hook | emits / does |
|---|---|
| `pytest_sessionstart` | `run_started` |
| `pytest_runtest_logstart(nodeid, location)` | `work_item_started` — `task_id`=`location[0]` (module file), `work_item_id`=`nodeid`, name=test name; remember started |
| `pytest_runtest_logreport(report)` | accumulate outcome: `failed` if any phase failed; `skipped` if skipped; else `passed`; stash a short failure repr |
| `pytest_runtest_logfinish(nodeid, location)` | `work_item_completed` (`task_id`/`work_item_id`, status=outcome); if failed, `message_added` (role `system`, the short repr); bump counters |
| `pytest_sessionfinish(session, exitstatus)` | `evidence_ready` (metrics: passed, failed, skipped, total, duration_s) + `run_completed` (status `failed` if failed>0 or exitstatus≠0 else `passed`); close the recorder |

State: `started: set[str]`, `outcomes: dict[str, str]`, `failures: dict[str,str]`,
counters `passed/failed/skipped`, `start_time`.

## Status mapping

| pytest | work_item status |
|---|---|
| passed | `passed` |
| failed / error (setup/call/teardown) | `failed` |
| skipped (incl. xfail) | `skipped` |
| xpassed | `passed` |

(The kit's work-item reducer maps envelope `status: "failed"` → failed, anything
else → completed; `skipped` renders as completed with the status carried for the
label.)

## Emitted stream

Canonical bare envelopes (the SDK default) — consumed by `intui watch <file>` /
`--follow` / scrub with no adapter. Modules nest as tasks via parent inference.

## Packaging

```toml
[project.entry-points.pytest11]
intui = "intui.pytest_plugin"
```

No new runtime dependency; `pytest` is present only when the plugin runs (already
a dev dependency for the project's own tests).

## What does NOT change

- Event envelope/vocabulary, store, reducers, selectors, widgets, the console,
  the emit SDK. Additive: one plugin module + one entry point.
