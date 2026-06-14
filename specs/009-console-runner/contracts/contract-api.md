# API Contract: Zero-Config Console Runner

**Feature**: `009-console-runner` | **Date**: 2026-06-14

The public surface this feature adds, and the behavioral guarantees tests pin.

## `intui.events` (engine-free) — new exports

### `NdjsonStreamSource`

```python
NdjsonStreamSource(
    lines: Path | str | Iterable[str] | AsyncIterable[str],
    *,
    event_record_types: tuple[str, ...] = (),
    rate: float | None = None,
) -> EventSource
```

Guarantees:
- Bare envelope lines are yielded unchanged.
- A wrapped record `{"type": R, "event": {…}}` with `R ∈ event_record_types`
  yields its inner `event`.
- A non-event record (type not in `event_record_types`, no envelope shape) is
  ignored.
- Invalid JSON / non-object lines yield `{"__malformed__", "line_number"}` (the
  store reports them via health; the run continues).
- Blank lines are skipped.
- Accepts a file path, a sync iterable of lines, or an async iterable of lines.

### `SubprocessSource`

```python
SubprocessSource(
    cmd: Sequence[str],
    *,
    event_record_types: tuple[str, ...] = (),
) -> EventSource
```

Guarantees:
- Spawns `cmd` with no shell; reads stdout ndjson via the same decode/unwrap
  rules as `NdjsonStreamSource`.
- Child EOF → iterator completes (caller marks ENDED).
- Spawn failure raises out of iteration (caller marks DISCONNECTED).
- Does not read the parent's stdin.

Both satisfy the existing `EventSource` Protocol; no `Store` change.

## `intui.kit.state` — promoted run-status slice

```python
run_status_slice() -> tuple[Reducer, str]      # (reducer, "idle")
RUN_STATUS_EVENT_TYPES: frozenset[str]
```

Guarantees:
- The reducer maps lifecycle/synthetic events to `ACTIVITY_STATES`
  (see data-model.md table) and passes unknown types through unchanged.
- `RUN_STATUS_EVENT_TYPES ⊆ KNOWN_EVENT_TYPES` (unioned in; drift-proof).

## `intui.console` (rendering layer) — new module

```python
from intui.console import ConsoleApp, build_console, watch

build_console(
    source: EventSource,
    *,
    public_safe: bool = True,
    sweep_seconds: float = 1.6,
) -> ConsoleApp

watch(
    source: EventSource | Path | str,
    *,
    public_safe: bool = True,
    rate: float | None = None,
) -> None
```

Guarantees:
- `ConsoleApp` renders activity strip + conversation + routable central view
  (tasks/lanes/diff/evidence) + command bar + footer with **no caller-provided
  reducers or widgets**.
- All four central views are reachable by keyboard (`t`/`l`/`d`/`e`) and via the
  command bar/palette.
- Public-safe by default; `public_safe=False` shows full diff/evidence values.
- These names are **not** importable from the `intui` root (engine-free
  boundary preserved).

## CLI

```text
intui watch [--public-safe | --no-public-safe] [--rate R] <file.jsonl>
intui watch [--public-safe | --no-public-safe] -- <command> [args…]
```

```python
from intui.console.cli import main
main(argv: list[str] | None = None) -> int
```

Guarantees:
- File form replays the file; `-- cmd…` spawns the command and watches stdout.
- `--no-public-safe` disables redaction; default is public-safe.
- A missing file or a command that cannot start yields `error: …` on stderr and
  a non-zero return code — never a traceback.
- Exposed as `[project.scripts] intui`, so `intui watch …` works after install.

## Backward compatibility

- Purely additive. No existing signature changes.
- The `operator_console` example is refactored to import `run_status_slice`
  instead of defining its own reducer — identical behavior (no contract change
  for the example's stream).
