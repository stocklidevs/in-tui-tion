# API Contract: Live Follow & Record

**Feature**: `016-follow-and-record` | **Date**: 2026-06-14

New surface and guarantees tests pin. All additive.

## `NdjsonStreamSource` — follow

```python
NdjsonStreamSource(path, *, event_record_types=(), rate=None,
                   follow=False, poll_interval=0.25)
```

Guarantees:
- `follow=True` (path): yields existing lines, then keeps yielding appended lines;
  the stream stays LIVE (never ends at EOF) until the consumer stops.
- A line appended without its trailing newline is yielded **once**, after the
  newline arrives (no partial/duplicate events).
- Reuses decode/unwrap + the `{"__malformed__"}` marker for bad lines.
- Cancels cleanly (closes the file handle) when the consuming worker stops.
- Engine-free.

## `Store.events`

```python
Store.events -> tuple[Event, ...]   # accepted events, in order (read-only)
```

Guarantees: returns the accepted events; no mutation; engine-free.

## `ConsoleApp` — record

Guarantees:
- A record key (`ctrl+s`, footer-visible) writes the accepted events to a
  timestamped `.jsonl` (`intui-recording-<ts>.jsonl`, cwd) via `write_recording`
  and reports the path.
- The file is **canonical** envelopes (no wrapper) regardless of source/adapter,
  so `intui watch <file>` replays it with no `--adapter`.
- A write failure is reported (notify), not raised.

## Front doors

```python
watch(source, *, public_safe=True, rate=None, follow=False) -> None
```

```text
intui watch --follow <file>      # follow the file
intui watch --follow -- <cmd>    # error: follow is for a file
```

Guarantees: `--follow` enables follow for the file form; combined with a command
it is a clear error (non-zero, message — not a traceback).

## Backward compatibility

- Purely additive: two defaulted `NdjsonStreamSource` params, a `Store.events`
  property, a `ConsoleApp` binding/action, and `watch`/CLI `--follow`. No existing
  signatures change; recording format unchanged.
