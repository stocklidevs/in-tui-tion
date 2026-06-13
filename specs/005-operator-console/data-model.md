# Data Model: Operator Console

**Feature**: `005-operator-console` | **Date**: 2026-06-13

Engine-free, immutable dataclasses with value equality.

## Modes

### ModeState (slice)

| Field | Type | Notes |
|-------|------|-------|
| `modes` | tuple[str, ...] | Ordered mode names (seeded at slice creation). |
| `current` | str | Active mode; defaults to the first seeded mode. |

### Standard event mapping

| Event type | Effect |
|------------|--------|
| `mode_changed` | If `payload["mode"]` is a known mode, set `current` to it; unknown → unchanged. |
| anything else | unchanged. |

`mode_slice(modes, initial=None)` → `(reducer, ModeState(modes, initial or modes[0]))`.

### ModeView

`entries: tuple[ModeEntry, ...]` where `ModeEntry(name, active)`. Memoized
selector `mode_view(slice="modes")`.

### switch_mode intent

`switch_mode_intent(mode: str) -> Intent` → `Intent("switch_mode",
{"mode": mode})`. The app handler appends a `mode_changed` event with that
mode (intent → event → state; FR-011). Not risky.

## Conversation

### ConversationEntry

| Field | Type | Notes |
|-------|------|-------|
| `order` | int | Arrival index (stable ordering). |
| `role` | str | `agent | user | system | unknown` (unknown for unrecognized roles). |
| `kind` | enum: `message | question | approval` | From the event type. |
| `text` | str | The message/question/approval text. |

### ConversationState (slice)

`entries: tuple[ConversationEntry, ...]` — append-only in arrival order.

### Standard event mapping

| Event type | Effect |
|------------|--------|
| `message_added` | Append entry, kind=message, role from `payload["role"]` (unknown roles kept as `unknown`). |
| `question_requested` | Append entry, kind=question, role=agent. |
| `approval_requested` | Append entry, kind=approval, role=agent. |
| anything else | unchanged. |

`conversation_slice()` → `(reducer, ConversationState())`.

### ConversationView

`entries: tuple[ConversationRow, ...]` where
`ConversationRow(order, role, kind, text, tag)` — `tag` is the non-color
role/kind label (e.g. `agent`, `you`, `system`, `? question`, `approval`).
Memoized selector `conversation_view(slice="conversation")`.

## Components (presentation contracts)

- **ModeStrip**: a row `…  ▸ Build   Inspect   …` — active mode marked with a
  `▸` (non-color counterpart) plus emphasis; each mode's shortcut posts a
  `switch_mode` intent. Renders `mode_view`.
- **ConversationLog**: a scrollable transcript; each row `‹tag› text`, kept
  scrolled to the latest; empty state `no messages`. Renders
  `conversation_view`.

## Presentation rules

- Mode entry: active `▸ {name}`, inactive `  {name}`; marker is the non-color
  counterpart (SC-004).
- Conversation tags: `agent:`/`you:`/`system:`/`? question:`/`approval:` — kind
  is identifiable from text alone (SC-002). Unknown role → `({role}):`.
- Empty states: no modes → nothing; empty conversation → `no messages`.
