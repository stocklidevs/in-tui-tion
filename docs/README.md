# in-TUI-tion docs

Start here:

- **[Quickstart](quickstart.md)** — watch a stream, emit one, or build in code.
- **[Event-stream contract](event-stream-contract.md)** — the canonical event
  vocabulary every producer targets (single source of truth).
- **[JSON Schema](contracts/event-envelope.schema.json)** — the envelope schema.

## Capability guides (per-feature quickstarts)

- [Zero-config runner](../specs/009-console-runner/quickstart.md) — `intui watch`
  / `watch()` / `ConsoleApp`.
- [IntentForge adapter](../specs/010-intentforge-adapter/quickstart.md) —
  `--adapter intentforge`.
- [Producer SDK](../specs/012-producer-sdk/quickstart.md) — `run_recorder`.
- [Workspace file tree](../specs/013-workspace-file-tree/quickstart.md).
- [File actions as intents](../specs/014-file-actions-intents/quickstart.md).
- [Process metrics monitor](../specs/015-process-metrics-monitor/quickstart.md) —
  `--metrics`.
- [Live follow & record](../specs/016-follow-and-record/quickstart.md) —
  `--follow` + `ctrl+s`.
- [Time-travel scrubber](../specs/017-time-travel-scrubber/quickstart.md) —
  pause / step / rewind.

## Reference

- [Architecture & layers](../README.md#architecture)
- [Constitution (governance principles)](../.specify/memory/constitution.md)
- [Changelog](../CHANGELOG.md)

Every feature also has a full spec/plan/tasks under
[`specs/`](../specs/) (GitHub Spec Kit).
