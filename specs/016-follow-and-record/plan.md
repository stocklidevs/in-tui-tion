# Implementation Plan: Live Follow & Record

**Branch**: `016-follow-and-record` | **Date**: 2026-06-14 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/016-follow-and-record/spec.md`

## Summary

Two thin live ergonomics:

1. **Follow (tail)** — `NdjsonStreamSource(path, follow=True, poll_interval=…)`:
   read existing lines, then keep yielding appended lines (buffering partial
   lines until a newline arrives), staying live forever until the consumer stops.
   Reuses the existing `_decode_ndjson_line` (unwrap + malformed handling).
   Exposed via `watch(..., follow=…)` and `intui watch --follow <file>`
   (`--follow` with `-- <cmd>` is a clear error).
2. **Record** — `Store.events` (read-only accepted events) + a `ConsoleApp`
   record key (`ctrl+s`) that writes those events to a timestamped canonical
   `.jsonl` via the existing `write_recording`, reporting the path. Recorded
   files are canonical (no wrapper), so they replay with no adapter; a failed
   write is reported, not fatal.

Decisions in [research.md](research.md); shapes in [data-model.md](data-model.md);
surface in [contracts/contract-api.md](contracts/contract-api.md).

## Technical Context

**Language/Version**: Python 3.11–3.13 (unchanged).

**Primary Dependencies**: Textual 6.x (the record key on `ConsoleApp`). No new
deps (follow uses stdlib `asyncio`/`io`; record uses the existing writer).

**Storage**: ndjson (followed input; recorded output).

**Testing**: pytest headless for follow (write a temp file, drive the source,
append lines, assert new events reduce, then cancel; partial-line case) and
`Store.events`; Pilot for the `ConsoleApp` record action (events → press key →
file written → round-trips on replay; adapted source → canonical output); a CLI
test for `--follow` wiring + the `--follow -- cmd` error.

**Target Platform**: unchanged. Tail uses text-mode `readline` polling
(cross-platform); no OS-specific file-watch API.

**Project Type**: library + examples gallery (unchanged).

**Performance Goals**: follow polls on a small interval (default 0.25s) and is
non-blocking; idle when the file isn't growing.

**Constraints**: follow + `Store.events` engine-free (layering guard); recorded
output canonical (replayable, no adapter); follow cancels cleanly on app quit;
record never crashes the app on a bad path.

**Scale/Scope**: `follow` param + tail helper on the existing source; a
`Store.events` accessor; a `ConsoleApp` record action + binding; `watch`/CLI
flags; docs. Out of scope: wait-for-file-to-appear, log rotation/truncation
handling, continuous tee-to-file (record is a snapshot), custom record path UX.

## Constitution Check

| # | Principle | Status | Notes |
|---|-----------|--------|-------|
| I | Structured State | ✅ PASS | Follow feeds the same pipeline; record dumps accepted events. |
| II | Layered Architecture | ✅ PASS | Follow + `Store.events` engine-free; only the record key touches the app layer. |
| III | Actions Are Intents | ✅ PASS | Record writes a file the user explicitly requested via a key; reads the store, no app-state mutation. |
| IV | Keyboard-First | ✅ PASS | Record is a footer-visible key; follow needs no UI. |
| V | Meaningful Motion | ✅ PASS (n/a) | — |
| VI | Public-Safe | ✅ PASS | Recorded events are the canonical accepted events (already what the contract intends); no new exposure. |
| VII | Test-First, Replayable | ✅ PASS | Follow + record headless/Pilot test-first; recorded files replay deterministically. |
| VIII | Example-Driven | ✅ PASS | Documented in quickstart/README; the existing examples gain follow/record usage notes. |
| — | New deps justified | ✅ PASS | None. |

**Post-Phase-1 re-check (2026-06-14)**: no new deps; layering holds. GATE: PASS —
Complexity Tracking empty.

## Project Structure

```text
src/intui/events/sources.py   # NdjsonStreamSource: + follow, poll_interval; _aiter_followed_lines
src/intui/state/store.py      # + events property (-> stream.events)
src/intui/console/runner.py   # watch(..., follow=False) passthrough
src/intui/console/cli.py      # --follow (file form; error with `-- cmd`)
src/intui/console/app.py      # ConsoleApp record action (ctrl+s) + binding

tests/
├── unit/
│   ├── test_sources_ndjson.py   # (extend) follow: initial + appended + partial line + cancel
│   ├── test_store.py            # (extend, or new) Store.events accessor
│   └── test_console_cli.py      # (extend) --follow wiring + `--follow -- cmd` error
└── integration/
    └── test_console_app.py      # (extend) record action writes a replayable canonical file

docs/quickstart.md  README.md   # --follow + record key
```

**Structure Decision**: follow is a mode on the existing `NdjsonStreamSource`
(smallest surface, reuses decode/unwrap); record is a `ConsoleApp` action over a
new read-only `Store.events` accessor using the existing `write_recording`. No new
modules.

## Complexity Tracking

No constitutional violations — table intentionally empty.
