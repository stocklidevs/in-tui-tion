# in-TUI-tion

[![PyPI version](https://img.shields.io/pypi/v/intui.svg)](https://pypi.org/project/intui/)
[![Python versions](https://img.shields.io/pypi/pyversions/intui.svg)](https://pypi.org/project/intui/)
[![CI](https://github.com/stocklidevs/in-tui-tion/actions/workflows/ci.yml/badge.svg)](https://github.com/stocklidevs/in-tui-tion/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Types: mypy](https://img.shields.io/badge/types-mypy-blue.svg)](https://mypy-lang.org/)
[![Linting: Ruff](https://img.shields.io/badge/lint-ruff-261230.svg)](https://github.com/astral-sh/ruff)
[![Built with Textual](https://img.shields.io/badge/built%20with-Textual-5a4fcf.svg)](https://textual.textualize.io/)

**Point it at an event stream, get a rich terminal console — with zero UI code.**

in-TUI-tion is a Python library for building rich, first-class terminal user
interfaces on top of [Textual](https://textual.textualize.io/). Your tool
describes what happens as an **append-only event stream**; the library reduces it
into **immutable state**, projects **view models**, and renders **self-updating
widgets** — tasks, diffs, a file tree, evidence, resource metrics, a conversation,
and a signature activity strip. User input flows back as **named intents**; the
library never mutates your state, and every run **replays deterministically**, so
you can even pause and rewind time.

![the console showing a run's diff, tasks and activity strip](https://raw.githubusercontent.com/stocklidevs/in-tui-tion/main/docs/media/console.svg)

```text
your tool -> event stream -> reducer/state store -> view models -> widgets
   ^                                                                   |
   +---------- intents <- user input <- (the library never mutates) <--+
```

## Install

```sh
pip install intui                 # or: uv add intui
pip install "intui[metrics]"      # + psutil, for process metrics
```

Python 3.11+, a modern terminal, fully typed (`py.typed`).

## Watch a stream — zero code

```sh
intui watch run.jsonl                          # replay a captured run
intui watch -- my-agent --json                 # spawn a producer, watch it live
intui watch --follow run.jsonl                 # tail a growing stream
intui watch --metrics -- python build.py       # watch a command's CPU/memory
intui watch --adapter intentforge run.ndjson   # normalize an IntentForge run
```

In the console: `t/l/f/d/e/m` switch views (tasks, lanes, files, diff, evidence,
metrics) · `space ,/. home/end` **time-travel** (pause, step, rewind, resume) ·
`ctrl+s` saves the run to a replayable file · `ctrl+p` the command palette.

## Produce a stream — a few lines, no JSON by hand

```python
from intui import run_recorder

with run_recorder("run.ndjson") as rec, rec.run():
    with rec.task("build", "Build the app") as build:
        with build.work_item("compile"):
            rec.file_written("src/app.py", change_type="added")
            rec.diff("src/app.py", before=old, after=new)
    rec.evidence(pass_rate="92%", certified="gold")
```

Then `intui watch run.ndjson` (or pipe it live: `intui watch -- python my_tool.py`).
The SDK emits the canonical
[event-stream contract](docs/event-stream-contract.md), so the runner reads it
with no adapter.

## What you get

| Capability | What it does |
|---|---|
| **Zero-config console** | `intui watch` / `watch()` / `ConsoleApp` render any compliant stream — file replay or a live subprocess. |
| **Producer SDK** | `run_recorder` emits canonical events (tasks, work items, diffs, evidence, files, messages, metrics) in a few lines. |
| **Task / lane views** | A counter chip, a nested task/work-item tree (parents inferred), and parallel lanes. |
| **Diffs** | A changed-file list + green/red diff that **accumulates** across many `file_diff` events. |
| **Workspace file tree** | A keyboard-navigable tree of the files a run produced; open/copy/delete surfaced as **intents** your app fulfills. |
| **Evidence panel** | Labeled outcome metrics. |
| **Process metrics** | `--metrics` spawns a command and shows status, duration, CPU, memory + sparklines (via `psutil`). |
| **Time-travel scrubber** | Pause / step / rewind / resume — every panel shows the run *as it was* (it's just `reduce(events[:n])`). |
| **Follow & record** | Tail a growing file (`--follow`); `ctrl+s` saves the run to a canonical, replayable `.jsonl`. |
| **IntentForge adapter** | `--adapter intentforge` normalizes IF's run-trace stream into the canonical vocabulary. |
| **Public-safe by default** | Diffs, evidence, and paths are redacted unless you opt out. |

Producers whose event names differ are normalized by a thin **adapter**; the
canonical vocabulary every producer targets is the single source of truth in
[docs/event-stream-contract.md](docs/event-stream-contract.md).

## Gallery

<table>
<tr>
<td width="50%"><b>Tasks &amp; work items</b><br><img src="https://raw.githubusercontent.com/stocklidevs/in-tui-tion/main/docs/media/tasks.svg" alt="tasks view"></td>
<td width="50%"><b>Workspace file tree</b><br><img src="https://raw.githubusercontent.com/stocklidevs/in-tui-tion/main/docs/media/files.svg" alt="file tree view"></td>
</tr>
<tr>
<td><b>Diff viewer</b><br><img src="https://raw.githubusercontent.com/stocklidevs/in-tui-tion/main/docs/media/diff.svg" alt="diff view"></td>
<td><b>Process metrics</b><br><img src="https://raw.githubusercontent.com/stocklidevs/in-tui-tion/main/docs/media/metrics.svg" alt="metrics view"></td>
</tr>
<tr>
<td><b>Evidence panel</b><br><img src="https://raw.githubusercontent.com/stocklidevs/in-tui-tion/main/docs/media/evidence.svg" alt="evidence view"></td>
<td><b>Time-travel scrubber</b><br><img src="https://raw.githubusercontent.com/stocklidevs/in-tui-tion/main/docs/media/scrubber.svg" alt="time-travel scrubber (paused)"></td>
</tr>
</table>

## Architecture

1. **Core** (`intui.events/state/viewmodels/actions/theming`, `intui.kit.state`,
   `intui.adapters`) — the engine-free pipeline: envelopes, streams, reducers,
   immutable snapshots, selectors, intents, themes, producer adapters. Imports no
   terminal engine (enforced by lint + a layering test).
2. **Rendering** (`intui.widgets`, `intui.app`) — Textual-based bound
   widgets/containers, a render-coalescing bridge, the Signal motion primitive,
   and the app shell with risky-action confirmation.
3. **Kit** (`intui.kit`) — the high-level components above over a shared
   engine-free state model.
4. **Producer SDK** (`intui.emit`) and the **console runner** (`intui.console`).
5. **Examples** (`examples/`) — first-class runnable demos of every feature.

## Quickstart & examples

Full guide: **[docs/quickstart.md](docs/quickstart.md)** · docs index:
**[docs/README.md](docs/README.md)**.

```sh
uv sync
uv run python -m examples.operator_console     # the flagship: whole kit + modes
uv run python -m examples.intentforge_console  # a real IntentForge run, adapted
uv run python -m examples.emit_demo            # produce a stream with the SDK
uv run python -m examples.process_monitor      # watch a command's resources
uv run pytest                                  # headless test suite
```

## Project governance

Spec-driven (GitHub Spec Kit): specs, plans, and tasks live under `specs/`;
principles live in
[.specify/memory/constitution.md](.specify/memory/constitution.md). Changes:
[CHANGELOG.md](CHANGELOG.md). Licensed under [MIT](LICENSE).
