# Data Model: Stream Contract & Packaging

**Feature**: `008-stream-contract-packaging` | **Date**: 2026-06-13

This feature is mostly contract + packaging; the "data" is the vocabulary
registry, the validator's issue type, and the metadata.

## Canonical event vocabulary

The set of event `type` values the **bundled** reducers consume. Declared per
module (the reducer uses the constant) and unioned into the registry.

| Module constant | Event types |
|---|---|
| `TASKBOARD_EVENT_TYPES` | `task_created`, `task_started`, `task_completed`, `task_blocked`, `work_item_started`, `work_item_completed`, `subagent_started`, `subagent_activity`, `subagent_completed` |
| `ARTIFACT_EVENT_TYPES` | `diff_ready`, `evidence_ready` |
| `CONVERSATION_EVENT_TYPES` | `message_added`, `question_requested`, `approval_requested` |
| `MODE_EVENT_TYPES` | `mode_changed` |
| `VIEW_EVENT_TYPES` | `view_selected` |
| `KNOWN_EVENT_TYPES` | frozenset(union of all the above) |

**Recommended lifecycle conventions** (documented, *not* reduced by a bundled
component — apps reduce these, e.g. to drive the activity strip): `run_started`,
`run_completed`, `run_failed`, `gate_started`, `gate_passed`, `gate_failed`.
These appear in the contract doc as conventions, not in `KNOWN_EVENT_TYPES`.

## Envelope (recap, the published schema)

`version` (`"1"`), `event_id`, `run_id`, `timestamp` (UTC ISO-8601), `type`,
`scope` (`session_id`/`task_id`/`work_item_id`/`lane_id` + extra), optional
`status`, `summary`, `payload`. `payload` may carry a `public_safe` flag;
evidence/diff renderers redact by default (Principle VI).

## StreamIssue

| Field | Type | Notes |
|---|---|---|
| `line` | int | 1-based line number (0 for non-line checks). |
| `severity` | `error` \| `warning` | envelope problems = error; unknown type = warning. |
| `reason` | str | human-readable. |
| `event_id` | str \| None | when known. |

## Validator API (engine-free, foundation)

```text
validate_event(data: Mapping, *, known_types: Set[str] | None = None)
    -> list[StreamIssue]
validate_stream(lines: Iterable[str] | Path, *, known_types=None,
                event_record_types: tuple[str,...] = ())
    -> list[StreamIssue]
```

- `validate_event`: envelope validation via `parse_event` (errors) + unknown
  `type` vs `known_types` (warning).
- `validate_stream`: per-line; blank lines skipped; JSON parse failure → error
  with line number. If `event_record_types` is given (e.g. a producer wraps
  events as `{"type":"run_trace_event","event":{...}}`), only those records are
  validated as events and others are ignored.

## Packaging metadata (pyproject `[project]`)

- `dynamic = ["version"]` + `[tool.hatch.version] path = "src/intui/__init__.py"`
- `description`, `readme`, `requires-python = ">=3.11"`, `license`
- `authors`, `keywords` (tui, terminal, textual, console, agent, dashboard)
- `classifiers` (Dev Status, Environment :: Console, Intended Audience,
  License, Programming Language :: Python 3.11/3.12/3.13, Topic :: Terminals,
  Typing :: Typed)
- `[project.urls]` Homepage, Repository
- `src/intui/py.typed` marker shipped in the wheel.

## Single version source

`src/intui/__init__.py`: `__version__ = "0.8.0"` — the only place; pyproject
reads it dynamically; `intui.__version__ == importlib.metadata.version(...)`.
