# Changelog

All notable changes to **in-TUI-tion** are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/), and the project adheres to
[Semantic Versioning](https://semver.org/).

## [1.2.0] - 2026-07-01

### Changed

- **Console UX redesign** — the run itself is now the interface. The side
  conversation column and the one-view-at-a-time router are replaced by a
  **single-column run timeline** (messages, task results, and failure callouts
  in arrival order, every row glyph+label) with a **prompt pinned to the
  bottom**. Slash commands (`/tasks /lanes /files /evidence /metrics /diff
  /scrub /save`) or the same single keys drive everything: diffs unfold
  **inline** (`d`), browsable panels open as **modal overlays** (Esc closes).
  A one-shot red flash lands with a new failure (honoring reduced motion);
  the KITT strip still tracks the run phase by color, glyph, and label.
  Pure rendering-layer change: events, state, reducers, and selectors are
  untouched, and recordings replay identically.

### Added

- `timeline_slice` reducer + `run_timeline_view` selector and
  `TimelineRow`/`TimelineFeedView` models (engine-free), plus the `RunTimeline`
  console widget. The timeline is reduced **directly from the stream in arrival
  order** (work items and tasks are single rows updated in place); a
  ``FAILED <ref>: detail`` message attaches to its failure row, which renders
  as a bordered callout with the detail inside.
- **Voice per row** — user messages are bright and tagged ``‹you›``, system
  lines dimmed and tagged ``‹system›``, the agent is the default voice; every
  row carries a ``+4.2s`` elapsed marker on the run's own clock.
- **Summary card in the flow** — ``evidence_ready`` renders as an
  accent-bordered card on the timeline (metrics joined ``label value · …``),
  values redacted by default (``run_timeline_view(public_safe=…)``).
- **Slash palette** — typing ``/`` in the prompt floats live-filtered command
  hints (with descriptions) above the input; a unique prefix resolves on
  submit (``/f`` → ``/files``). Overlays carry a clickable ``✕ close`` in the
  title bar. The footer shows only the essentials (the palette and ``ctrl+p``
  teach the rest).

## [1.1.0] - 2026-06-14

### Added

- **pytest plugin** — `pytest --intui[=PATH]` emits the canonical event stream as
  a suite runs (modules as tasks, tests as work items, failures in the
  conversation, a pass/fail/skip summary as evidence). Auto-discovered via the
  `pytest11` entry point and **inert unless `--intui` is given**; adds no runtime
  dependency. The output is ordinary canonical ndjson — `intui watch` /
  `--follow` / scrub it with no adapter. The first producer integration.

## [1.0.1] - 2026-06-14

### Fixed

- **DiffViewer** — streaming diffs one file at a time (e.g. an IntentForge run
  emitting one `file_diff` per file) no longer raises
  `textual._node_list.DuplicateIds`. `ListView.clear()` is asynchronous, so a
  rebuilt list briefly coexisted with the previous one; file-row ids are now
  keyed by a per-rebuild generation so they can never collide during the clear.

## [1.0.0] - 2026-06-14

First stable release. The full path from "an event stream" to "a rich,
replayable terminal console" — in both directions (consume and produce) — with a
public-safe, engine-free core and a Textual rendering layer.

### Added — consume

- **Zero-config runner** — `intui watch`, `watch()`, and `ConsoleApp` render any
  compliant stream (file replay or a live subprocess) with no application code.
- **IntentForge adapter** — `intui watch --adapter intentforge` normalizes IF's
  run-trace stream into the canonical vocabulary; verified against real IF output.
- **Workspace file tree** — a keyboard-navigable tree of the files a run produced,
  with open/copy/delete surfaced as intents the application fulfills (the library
  never mutates the filesystem).
- **Process metrics monitor** — `intui watch --metrics -- <cmd>` spawns a command
  and shows status, duration, CPU, memory + sparklines (optional `[metrics]`
  extra; `psutil`).
- **Time-travel scrubber** — pause, step, rewind, and resume a run; every panel
  shows the state as it was (`Store.snapshot_at` + `Timeline`).
- **Live follow & record** — `--follow` tails a growing stream file; `ctrl+s`
  saves the run to a canonical, replayable `.jsonl`.

### Added — produce

- **Producer SDK** (`intui.emit`, `run_recorder`) — emit canonical events (tasks,
  work items, diffs, evidence, files, messages, metrics) in a few lines, to a
  file, stdout, or a callback.

### Added — kit & contract

- Canonical event-stream contract + registry (`KNOWN_EVENT_TYPES`), an engine-free
  validator, and a published envelope JSON Schema.
- Components: task counter chip, task/work-item tree (parent inference),
  parallel lanes, command bar + palette, diff viewer (accumulating multi-file
  diffs), evidence panel, file tree, metrics panel, prompt input, activity strip,
  mode strip + conversation, and a central view router.
- Public-safety redactor (default-on) for diffs, evidence, and paths.

### Packaging

- Pip-installable with a single-source dynamic version, full metadata, `py.typed`,
  MIT license, an optional `metrics` extra, and the `intui` console entry point.

[1.0.0]: https://github.com/stocklidevs/in-tui-tion/releases/tag/v1.0.0
