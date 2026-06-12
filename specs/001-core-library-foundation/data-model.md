# Data Model: Core Library Foundation

**Feature**: `001-core-library-foundation` | **Date**: 2026-06-12

All pipeline entities are immutable (frozen dataclasses). Mutation happens
only by producing new values (new events appended, new snapshots reduced).

## Event

An append-only fact in a versioned envelope.

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `version` | str | yes | Envelope schema version; `"1"` for this feature. Unknown versions rejected on ingestion. |
| `event_id` | str | yes | Unique within a stream; duplicates ignored on append (FR-002). |
| `run_id` | str | yes | Identifies the run/session the event belongs to. |
| `timestamp` | datetime (UTC, ISO 8601 in serialized form) | yes | Producer-assigned. |
| `type` | str | yes | Open vocabulary; unknown types flow through reduction untouched (US1-3). |
| `scope` | Scope | yes | May be empty; see Scope. |
| `status` | str | no | Producer-declared status hint (e.g., `running`, `passed`). |
| `summary` | str | no | One-line human-readable description. |
| `payload` | mapping (JSON-serializable) | no | Type-specific data; may carry `public_safe` metadata, which the pipeline preserves untouched (Principle VI scoping). |

**Validation**: on ingestion — known `version`; non-empty `event_id`,
`run_id`, `type`; parseable timestamp; JSON-serializable payload. Validation
failure → the event is reported (id + cause) via StreamHealth and excluded;
the stream and UI continue (US2-4, FR-008 analog for parse errors).

## Scope

Identifies what an event is about. All fields optional strings:
`session_id`, `task_id`, `work_item_id`, `lane_id`. Extensible mapping for
adapter-specific keys.

## EventStream

Ordered, append-only sequence of accepted Events.

- **Fields**: `events` (ordered, immutable view), `seen_ids` (dedupe set),
  `health` (StreamHealth).
- **Invariants**: append-only (no mutation/removal of accepted events);
  `event_id` unique (duplicates silently dropped, counted in health);
  ordering = arrival order.

## StreamHealth

Derived health of the stream's source.

- **Fields**: `state` (enum: `live | ended | disconnected | erroring`),
  `last_event_at` (datetime | null), `rejected_count` (int),
  `last_error` (struct: `event_id`, `reason`) | null.
- **Transitions**: `live → ended` (source EOF), `live → disconnected`
  (source lost), any → `erroring` while rejections occur, `erroring → live`
  on next accepted event. Surfaced to apps as a built-in view model (FR-007).

## Reducer

Application-declared pure function: `(Snapshot, Event) → Snapshot`.

- **Rules**: pure/deterministic (FR-003); unknown event types MUST return the
  snapshot unchanged; exceptions are isolated by the Store — the event is
  recorded as failed (id + cause) in StreamHealth and the prior snapshot is
  retained (FR-008).
- **Composition**: reducers compose (each owns a state slice); composition is
  itself a Reducer.

## Snapshot

Immutable application state at a point in the stream.

- **Fields**: `state_version` (int, monotonically increasing per accepted
  event), application state slices (app-defined, immutable), `health`
  (StreamHealth).
- **Invariants**: same event sequence ⇒ equal snapshots (SC-002); equality is
  structural (cheap replay assertions).

## Store

The only stateful pipeline object: holds current Snapshot, applies the
composed Reducer per accepted event, publishes change notifications
(snapshot + state_version) to subscribers. Engine-agnostic and synchronous;
the Textual bridge subscribes like any other consumer.

## ViewModel (Selector)

Pure projection `Snapshot → ViewModel` consumed by widgets.

- **Rules**: presentation-shaped (FR-004); memoized per `state_version`;
  value-equality drives re-render decisions (only widgets whose view model
  changed re-render — US1-2).

## Intent (Action)

Named user-triggered request delivered to the application handler.

| Field | Type | Notes |
|-------|------|-------|
| `name` | str | e.g., `approve`, `toggle_item` |
| `payload` | mapping | declared by the binding widget |
| `risky` | bool | `true` ⇒ confirmation required before delivery (FR-016) |

- **Lifecycle**: `created → (confirming → confirmed | cancelled) → delivered`.
  Non-risky intents skip the confirming states. Delivery is to the app's
  async IntentHandler; the library never mutates app state (FR-014).

## Theme

Named token set applied application-wide (FR-017).

- **Fields**: `name`, `palette` (background/surface/text tiers), `emphasis`
  (accent/muted), `status_colors` (mapping status name → color, e.g.,
  thinking/waiting/verifying/success/history/failure).
- **Rules**: switching themes re-styles all themed widgets with no widget
  code changes; one default theme ships with the library.

## Signal

Status-driven visual primitive (FR-018, Principle V).

- **Fields**: `status_field` (selector binding), `status_styles` (mapping
  status → {color token, motion mode, glyph/text counterpart}), current
  status (derived, never set directly).
- **Motion modes**: `steady`, `pulse`, `swoosh`, `strobe`.
- **Rules**: appearance derives exclusively from the bound state field;
  every status style MUST define a non-color counterpart (SC-006); on
  reduced-color terminals the glyph/text counterpart remains.

## Recording

JSONL serialization of an EventStream (one envelope per line, UTF-8).

- **Rules**: lossless round-trip (write → read → identical accepted events);
  replay through the pipeline yields snapshots identical to the original run
  (FR-006); malformed lines reported with line number + reason, reader
  continues or halts per caller choice (US2-4).

## EventSource (protocol)

Async iterator of envelopes + terminal health outcome. Implementations in
this feature: in-memory sequence (tests), JSONL file replay (with optional
pacing). Live external sources (process attach, network) are out of scope but
MUST be implementable against this protocol unchanged (spec Assumptions).

## Relationships

```text
EventSource ──envelopes──▶ EventStream ──accepted Events──▶ Store(Reducer)
                                │                              │
                          StreamHealth ◀───── isolation ───────┤
                                                               ▼
Widgets ◀──changed ViewModels── Selectors(memoized) ◀────── Snapshot
   │
   └──user input──▶ Intent ──(confirm if risky)──▶ IntentHandler (app)
                                                       │
                                                       └──new events──▶ EventSource
```
