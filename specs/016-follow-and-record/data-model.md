# Data Model: Live Follow & Record

**Feature**: `016-follow-and-record` | **Date**: 2026-06-14

No new events or state shapes — a source mode, a read-only accessor, and a
console action.

## Follow mode (`NdjsonStreamSource`)

```text
NdjsonStreamSource(
    lines: Path | str | Iterable[str] | AsyncIterable[str],
    *,
    event_record_types: tuple[str, ...] = (),
    rate: float | None = None,
    follow: bool = False,          # NEW
    poll_interval: float = 0.25,   # NEW (follow poll cadence)
)
```

Behavior with `follow=True` (path input):
- Read and yield existing lines (decoded as today), then **keep** reading: loop
  `readline()`, buffering a partial line until it ends with `\n`, yielding each
  complete decoded line; sleep `poll_interval` when no new data.
- Never ends at EOF → the stream stays LIVE until the consumer stops; cancels
  cleanly (the file handle closes).
- `follow=True` with a non-path input is ignored (nothing to tail) — it behaves
  like the finite iterable.

## `Store.events` (read-only accessor)

```text
Store.events -> tuple[Event, ...]      # the accepted events, in order
```

Delegates to `EventStream.events`. Used by the record action; does not mutate.

## Record action (`ConsoleApp`)

```text
BINDINGS += ("ctrl+s", "record", "Save run")
ConsoleApp.action_record() -> None
```

- Writes `Store.events` to `intui-recording-<YYYYmmdd-HHMMSS>.jsonl` in the cwd
  via `write_recording`; notifies the path.
- Output is canonical bare envelopes (regardless of source/adapter) → replays
  with `intui watch <file>`.
- A write failure is caught and surfaced via `notify` (no crash).

## Front-door wiring

```text
watch(source, *, public_safe=True, rate=None, follow=False)   # follow for path sources
intui watch --follow <file>     # NdjsonStreamSource(path, follow=True)
intui watch --follow -- <cmd>   # clear error (follow is for a file)
```

## What does NOT change

- Event envelope/vocabulary, reducers, selectors, widgets, the recording
  format/writer. Additive: two source params, one `Store` accessor, one console
  action/binding, and `watch`/CLI flags.
