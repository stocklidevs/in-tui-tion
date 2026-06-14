# Implementation Plan: Zero-Config Console Runner

**Branch**: `009-console-runner` | **Date**: 2026-06-14 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/009-console-runner/spec.md`

## Summary

The "toothbrush" feature: render a full console from a canonical stream with
**zero application code**. Three deliverables on top of the existing kit:

1. **Engine-free stream sources** in `intui.events`: `NdjsonStreamSource`
   (over a line iterable or a file; unwraps wrapped records, ignores non-event
   records) and `SubprocessSource` (spawn a command, yield its stdout ndjson
   live). Both are `EventSource`s — they slot into the existing `Store.run`.
2. A **batteries-included `ConsoleApp`** (Textual layer, new `intui.console`
   subpackage) that wires the canonical slices (taskboard, artifacts,
   conversation, view routing, run-status) into a default layout — activity
   strip + conversation + routable central view + command bar — public-safe by
   default. Plus a `watch(source)` one-liner and `build_console(...)` factory.
3. An **`intui watch` CLI** (console entry point) that renders a `.jsonl` file
   (replay) or `-- <command…>` (subprocess), with `--public-safe/--no-public-safe`
   and `--rate`, and clear errors (no tracebacks) on bad input.

To keep `ConsoleApp` free of app code, the run-status reducer that drives the
KITT strip (today living in the `operator_console` example) is **promoted into
engine-free `intui.kit.state`** as `run_status_slice()`. The flagship example is
refactored to consume it (no behavior change), proving deduplication.

Decisions in [research.md](research.md); shapes in [data-model.md](data-model.md);
surface in [contracts/contract-api.md](contracts/contract-api.md).

## Technical Context

**Language/Version**: Python 3.11–3.13 (unchanged).

**Primary Dependencies**: Textual 6.x (runtime, unchanged). **No new runtime
deps** — sources use stdlib `asyncio`/`json`; the CLI uses stdlib `argparse`.

**Storage**: JSONL (unchanged).

**Testing**: pytest headless for the sources (line iterable + a tiny spawned
Python one-liner) and the run-status slice; Pilot (`app.run_test()`) for
`ConsoleApp` rendering + keyboard navigation + public-safe toggle; a CLI
argument-parsing/error-path test invoking `main([...])` directly.

**Target Platform**: Windows/macOS/Linux/WSL (subprocess uses
`asyncio.create_subprocess_exec`; tests spawn `sys.executable -c …` for
portability — no shell, no platform-specific binary).

**Project Type**: library + examples gallery (unchanged).

**Performance Goals**: live ingestion is non-blocking (driven by the existing
async worker); render coalescing unchanged.

**Constraints**: sources MUST be engine-free (lint ban + layering guard,
Principle II/VII); `ConsoleApp`/`watch`/CLI live in `intui.console` and are NOT
re-exported from the engine-free `intui` root (importing `intui` must stay
Textual-free). The runner never reads the terminal's stdin for events
(FR-010). Console nav is fully keyboard-operable (Principle IV).

**Scale/Scope**: sources + ConsoleApp + watch + CLI + entry point + run-status
slice promotion + a canonical demo fixture. Out of scope: the IntentForge
adapter (feature 010), `--follow`/file-tailing, live process attach to a
running PID, run comparison, PyPI upload.

## Constitution Check

| # | Principle | Status | Notes |
|---|-----------|--------|-------|
| I | Structured State | ✅ PASS | Everything shown derives from the snapshot; run-status becomes a first-class slice. |
| II | Layered Architecture | ✅ PASS | Sources engine-free in `intui.events`; ConsoleApp/CLI in `intui.console` (rendering layer); no inverted deps; root stays Textual-free. |
| III | Actions Are Intents | ✅ PASS | View navigation routes through `select_view_intent` → event → state, reusing the existing handler pattern. |
| IV | Keyboard-First, Accessible | ✅ PASS | Command bar + palette + footer; all views reachable by key; non-color activity glyph/label retained. |
| V | Meaningful Motion | ✅ PASS | Reuses the ActivityStrip; motion reflects real run state via the promoted reducer. |
| VI | Public-Safe | ✅ PASS | ConsoleApp public-safe by default; `--no-public-safe` is the explicit opt-out (FR-003). |
| VII | Test-First, Replayable | ✅ PASS | Sources + slice headless test-first; ConsoleApp via Pilot; CLI via `main([...])`. |
| VIII | Example-Driven | ✅ PASS | The runner itself is the zero-code "example"; ships a canonical demo fixture + quickstart; flagship refactored to reuse the promoted slice. |
| — | New deps justified | ✅ PASS | None — stdlib only. |

**Post-Phase-1 re-check (2026-06-14)**: no new deps; layering holds (sources
import only stdlib; ConsoleApp imports the kit downward). GATE: PASS —
Complexity Tracking empty.

## Project Structure

### Documentation (this feature)

```text
specs/009-console-runner/
├── plan.md  research.md  data-model.md  quickstart.md
├── contracts/contract-api.md
├── checklists/requirements.md
└── tasks.md (Phase 2 via /speckit-tasks)
```

### Source / repo changes

```text
src/intui/
├── events/
│   ├── sources.py          # + NdjsonStreamSource, SubprocessSource
│   └── __init__.py         # export the new sources
├── kit/state/
│   ├── run_status.py       # NEW — RUN_STATUS_EVENT_TYPES + run_status_slice()
│   └── __init__.py         # + run_status_slice / RUN_STATUS_EVENT_TYPES; union into KNOWN_EVENT_TYPES
└── console/                # NEW subpackage (rendering layer)
    ├── __init__.py         # export ConsoleApp, watch, build_console
    ├── app.py              # ConsoleApp(IntuiApp) + build_console()
    ├── runner.py           # watch(source) one-liner
    └── cli.py              # main(argv) — `intui watch` (argparse)

pyproject.toml              # + [project.scripts] intui = "intui.console.cli:main"

examples/operator_console/app.py  # refactor: import run_status_slice (no behavior change)

docs/quickstart.md          # + a "zero-config runner" section (intui watch / watch())

examples/operator_console/recording.jsonl  # reuse as the canonical demo fixture
  (or a small dedicated specs fixture for tests)

tests/
├── unit/
│   ├── test_sources_ndjson.py     # unwrapping, ignore non-event, malformed, path + iterable
│   ├── test_sources_subprocess.py # spawn python -c, consume lines, exit reflected
│   ├── test_run_status_slice.py   # lifecycle → activity states
│   └── test_console_cli.py        # main([...]) arg parsing + clear errors (missing file/cmd)
├── integration/
│   └── test_console_app.py        # Pilot: renders fixture, key-nav views, public-safe toggle, stream-end
└── unit/test_layering.py          # (existing) extended: sources stay engine-free
```

**Structure Decision**: new sources extend the existing engine-free
`intui.events.sources`; the batteries-included app, one-liner, and CLI live in a
new `intui.console` subpackage (rendering layer, never imported by the root);
the run-status reducer is promoted to engine-free `intui.kit.state` so
`ConsoleApp` needs no application reducers and the flagship example dedupes onto
it. The CLI is wired as a `[project.scripts]` entry point so `intui watch …`
works after `pip install`.

## Complexity Tracking

No constitutional violations — table intentionally empty.
