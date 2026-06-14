# API Contract: IntentForge Adapter

**Feature**: `010-intentforge-adapter` | **Date**: 2026-06-14

The public surface this feature adds, and the behavioral guarantees tests pin.

## `intui.adapters` (engine-free) — new subpackage

```python
from intui.adapters import adapt_record, IntentForgeSource
# also: from intui.adapters.intentforge import adapt_record, IntentForgeSource
```

### `adapt_record`

```python
adapt_record(record: Mapping[str, Any], *, run_id: str = "intentforge") -> Event | None
```

Guarantees:
- Accepts a `run_trace_event` wrapper, a bare `{sequence,name,payload}`, or a
  `{"type":"summary","summary":{…}}` record.
- Returns a canonical `Event` per the mapping table (data-model.md) or `None`
  for an unknown/ignored `name`.
- Every returned `Event` has `version="1"`, a stable `event_id`
  (`f"if-{sequence}"` / `"if-summary"`), the given `run_id`, a deterministic
  monotonic `timestamp` (from `sequence`), and the correct `scope`.
- Never raises on missing/extra payload keys, missing/empty `diff`, or a partial
  summary (FR-004).
- Emits only canonical `type`s → output validates against `KNOWN_EVENT_TYPES`
  with zero envelope errors (FR-009).
- Pure/stateless: same input → same output (deterministic; Principle VII).

### `IntentForgeSource`

```python
IntentForgeSource(
    source: Path | str | Iterable[str] | AsyncIterable[str],
    *,
    run_id: str = "intentforge",
) -> EventSource

IntentForgeSource.from_command(
    cmd: Sequence[str], *, run_id: str = "intentforge"
) -> EventSource
```

Guarantees:
- Reads raw IF ndjson (file path, line iterable, or spawned command) and yields
  adapted canonical envelope mappings — **including** the trailing summary.
- Malformed lines yield the `{"__malformed__", "line_number"}` marker (store
  reports via health); unmapped records are skipped; neither crashes the run.
- Satisfies the existing `EventSource` Protocol — usable with `watch`,
  `build_console`, and `Store.run` unchanged.
- Engine-free (no Textual import; layering guard).

## `intui.console` — CLI extension

```text
intui watch [--adapter {none,intentforge}] [--public-safe|--no-public-safe]
            [--rate R] (<file> | -- <command>)
```

Guarantees:
- `--adapter intentforge` renders an IF stream (file replay or `-- intentforge …`
  subprocess) through the adapter; `none` (default) is unchanged 009 behavior.
- All other 009 CLI guarantees (clear errors, no tracebacks, public-safe
  default) hold.

## Backward compatibility

- Purely additive. The only change to existing code is extracting
  `SubprocessSource`'s line-reading into a shared helper — no signature or
  behavior change (covered by existing 009 subprocess tests).
- IntentForge is not imported; coupling is to its on-the-wire JSON only.

## Out of scope (asserted by omission)

- No change to the canonical contract, the kit, or `ConsoleApp`.
- No stateful parent-linkage for assembly items (they render unassigned).
- No mapping of IF subcommands that don't emit the run-trace ndjson shape.
