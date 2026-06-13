# Data Model: Command Surfaces

**Feature**: `003-command-surfaces` | **Date**: 2026-06-12

Engine-free, immutable where it carries data. Availability rules are pure
callables over `Snapshot`.

## Command

| Field | Type | Notes |
|-------|------|-------|
| `id` | str | Stable identity; unique within a registry. |
| `label` | str | Human-readable name shown in both surfaces. |
| `key` | str \| None | Optional menu/binding key (e.g. `a`, `ctrl+d`). None = palette-only. |
| `intent` | Intent | The intent template delivered on invoke (carries its own `risky` flag). |
| `available` | Callable[[Snapshot], bool] | Pure availability rule; default always-available. |

`risky` is read from `intent.risky` — no separate flag (single source of truth).

## CommandRegistry

Ordered collection keyed by id.

- **Construction**: `CommandRegistry(commands)` — raises `ValueError` on
  duplicate ids.
- **Methods**:
  - `commands` → ordered tuple of `Command`
  - `get(id)` → Command
  - `is_available(id, snapshot)` → bool
- **Invariant**: ids unique; order is declaration order (presentation order).

## CommandView / CommandEntry

Per-state projection both surfaces consume (via a memoized selector).

```text
CommandView:
  entries: tuple[CommandEntry, ...]

CommandEntry:
  id: str
  label: str
  key: str | None
  risky: bool
  enabled: bool   # = registry.is_available(id, snapshot)
```

`command_view(registry)` is a `Selector[CommandView]` — memoized per snapshot
like every other kit selector.

## Matching (palette)

- `match_score(query: str, text: str) -> int | None` — case-insensitive
  subsequence match; returns a score (higher = better; contiguous runs and
  word-boundary starts score higher) or `None` for no match.
- `filter_commands(entries, query) -> tuple[CommandEntry, ...]` — keeps
  entries whose id or label matches, sorted by best score then registry order.
  Empty query returns all entries in registry order.

## PaletteState (transient UI state)

Local to the palette widget — never application state, never an event.

| Field | Type | Notes |
|-------|------|-------|
| `query` | str | Current typed text. |
| `results` | tuple[CommandEntry, ...] | Filtered + ranked entries. |
| `selected` | int | Index into `results`; clamped; resets to 0 on query change. |

## Invocation flow (both surfaces)

```text
user invokes entry
  -> re-check registry.is_available(id, current snapshot)   (FR-014)
       false -> drop, no delivery
       true  -> app.post_intent(command.intent)
                   -> risky? built-in ConfirmScreen (feature 001)
                              confirmed -> intent delivered to app handler
                              cancelled -> nothing
                   -> not risky -> intent delivered
```

Library code never mutates application state — invocation only ever results in
an `Intent` reaching the app's handler (Principle III, FR-006/013).

## Presentation rules

- Menu entry text: `{key}  {label}` (key omitted when None); disabled entries
  dimmed *and* marked (e.g. trailing/leading marker) so disabled state is not
  color-only (FR-015, SC-006).
- Overflow: when entries exceed width, render the first N that fit plus a
  trailing `… more` entry that opens the palette (FR-008).
- Palette row: `{key}  {label}` with the active selection marked by a caret/
  reverse style (visible focus, not color-only).
- Empty states: menu with no commands → explicit `no commands`; palette with
  no matches → explicit `no matching commands`.
