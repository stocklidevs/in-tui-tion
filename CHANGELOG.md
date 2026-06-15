# Changelog

All notable changes to **in-TUI-tion** are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/), and the project adheres to
[Semantic Versioning](https://semver.org/).

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
