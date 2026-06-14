# in-TUI-tion event-stream contract

The single source of truth for the data a producer emits to drive an in-TUI-tion
console. **Emit these JSON lines and the kit reduces them into a live console.**

A stream is **JSON Lines** (one JSON object per line, UTF-8). Each line is an
**event envelope**. Unknown event `type`s are tolerated (reducers pass them
through), so you can extend the vocabulary freely; the bundled components only
react to the canonical types below.

Validate a stream against this contract:

```python
from intui.events import validate_stream
from intui.kit.state import KNOWN_EVENT_TYPES

for issue in validate_stream("run.jsonl", known_types=KNOWN_EVENT_TYPES):
    print(issue.line, issue.severity, issue.reason)
```

## Envelope

Schema: [`docs/contracts/event-envelope.schema.json`](contracts/event-envelope.schema.json).

| Field | Required | Notes |
|-------|----------|-------|
| `version` | yes | Envelope schema version. Currently `"1"`. Unknown versions are rejected. |
| `event_id` | yes | Unique within a stream; duplicates are ignored (append-only dedupe). |
| `run_id` | yes | The run/session this event belongs to. |
| `timestamp` | yes | UTC ISO-8601 (e.g. `2026-06-13T10:00:00Z`). |
| `type` | yes | Event type — see the vocabulary below (open vocabulary). |
| `scope` | yes | `session_id` / `task_id` / `work_item_id` / `lane_id` (all optional) + adapter-specific keys. |
| `status` | no | Producer status hint (e.g. `running`, `passed`, `failed`). |
| `summary` | no | One-line human-readable description. |
| `payload` | no | Type-specific data; may carry a `public_safe` flag (see Public safety). |

## Canonical vocabulary (reduced by the bundled kit)

Mirrors `intui.kit.state.KNOWN_EVENT_TYPES`.

### Tasks & work (taskboard → chip / tree / lanes)
| `type` | scope | meaning |
|--------|-------|---------|
| `task_created` | `task_id` | a task exists (pending) |
| `task_started` | `task_id` | task active |
| `task_completed` | `task_id` | task done (`status: failed` → failed, else completed) |
| `task_blocked` | `task_id` | task blocked |
| `work_item_started` | `task_id`, `work_item_id` | work item active under its task (no `task_id` → `unassigned`) |
| `work_item_completed` | `task_id`, `work_item_id` | work item done (`status: failed` → failed) |
| `subagent_started` | `lane_id`, `task_id?` | a worker/lane started (payload `name`) |
| `subagent_activity` | `lane_id` | lane activity (`summary` = current activity) |
| `subagent_completed` | `lane_id` | lane terminal (`status`) |

### Artifacts (→ diff viewer / evidence panel)
| `type` | payload | meaning |
|--------|---------|---------|
| `diff_ready` | `title`, `unified` (unified-diff text) **or** `files` (structured); optional `public_safe` | the run's changed files |
| `evidence_ready` | `title`, `metrics` (`[{key,label,value,status?,unsafe?}]`); optional `public_safe` | outcome metrics |

### Conversation (→ conversation log)
| `type` | payload | meaning |
|--------|---------|---------|
| `message_added` | `role` (`agent`/`user`/`system`), `text` | a transcript message |
| `question_requested` | `text` | a clarifying question (agent) |
| `approval_requested` | `text` | an approval prompt (agent) |

### Modes & views (→ mode strip / view router)
| `type` | payload | meaning |
|--------|---------|---------|
| `mode_changed` | `mode` | active workflow mode changed |
| `view_selected` | `view` | central view changed |

## Recommended lifecycle conventions (app-reduced, not bundled)

These are not reduced by a bundled component, but examples use them (e.g. to
drive the activity strip). Emit them and reduce them in your app as you like:
`run_started`, `run_completed`, `run_failed`, `gate_started`, `gate_passed`,
`gate_failed`.

## Public safety (Principle VI)

Renderers of evidence and diffs **redact by default**: provider endpoints,
tokens, credentials, and absolute local paths are replaced with a `‹redacted›`
marker unless the consumer explicitly opts into a trusted-local view. Producers
may also mark an artifact or metric value unsafe (`public_safe: false` /
`unsafe: true`) to force redaction. Keep absolute paths and secrets out of
public streams regardless.

## Wrapped streams

Some producers wrap events as `{"type": "run_trace_event", "event": {…envelope…}}`
plus a trailing summary record. Validate those with:

```python
validate_stream(lines, known_types=KNOWN_EVENT_TYPES,
                event_record_types=("run_trace_event",))
```
