# Research & Decisions: Rich Incremental Diffs & Assembly Nesting

**Feature**: `011-rich-incremental-diffs` | **Date**: 2026-06-14

## D0 — Root cause (from the 010 real-data test)

Driving a real `intentforge assembly-benchmark --event-stream ndjson` run
(33 lines) through the 010 adapter showed: 20 `file_diff` events but the diff
view listed **1** file, and 6 assembly items rendered flat under "unassigned".
Cause confirmed in code: the artifacts reducer **replaces** the single diff
artifact on each `diff_ready`, and `tree_view` only nests items when a `TaskView`
exists for the parent. IF 0.9.13 (`3f1f6114`) now adds `suite_id` + `work_item_id`
to `assembly_item_*` and `suite_id` to runtime `file_diff` (verified in repo).

## D1 — Accumulate diffs by path (event-sourcing semantics), opt-out via `reset`

**Decision**: `diff_ready` merges its file(s) into the existing diff artifact
keyed by `raw_path` — a new path is appended (first-seen order), a seen path is
replaced in place. A `diff_ready` payload `reset: true` clears the accumulation
first. The artifact's id/title/public_safe come from the latest event.

**Why**: An event stream is append-only facts; `file_diff` means "this file
changed", so accumulating is the correct semantics and fixes the real IF case
(one `file_diff` per file). Keying by path makes re-emitting a file idempotent.
`reset` preserves a snapshot producer's ability to send a fresh full set. Evidence
keeps latest-wins (a summary *is* a snapshot), so only diffs change.

**Alternatives rejected**: (a) keep replace + require producers to batch all
files into one `diff_ready` — pushes work onto every producer and fights the
event model. (b) adapter-side buffering — `adapt_record` is pure/stateless per
record and shouldn't accumulate. (c) accumulate with no opt-out — a snapshot
producer would show stale files from older snapshots.

## D2 — Synthesize parent nodes in `tree_view`; carry `parent_id`

**Decision**: `tree_view` groups items by their actual `parent_key`. Real tasks
render with their items (unchanged). Remaining groups: a synthesized parent node
titled by the item's `parent_id` (status rolled up from its items), except the
genuine `UNASSIGNED_KEY` group which stays "unassigned". `WorkItemView` gains a
`parent_id` field (the raw parent id) set by `_reduce_item`, so the synthesized
node has a title.

**Why**: Producers that carry a parent on each item but emit no task lifecycle
event (real IF assembly streams) should still nest. Synthesizing from the data
already present avoids forcing the adapter to fabricate task events (which would
need state). Real task events still win (D-precedence), so nothing regresses for
producers that do emit tasks. Truly parentless items keep the "unassigned"
bucket.

**Alternatives rejected**: (a) make the adapter emit a synthetic `task_started`
for the suite — `adapt_record` is 1:1 and stateless; it can't dedupe "first time
seeing this suite", and emitting per-item would be hacky. (b) leave items
unassigned — loses the structure that makes a run readable (the reported pain).

## D3 — Parent status roll-up

**Decision**: a synthesized parent's status is the first present of
`failed → blocked → active → pending`, else `completed` (all items terminal).

**Why**: gives the synthesized node a meaningful glyph/label that reflects its
children without inventing a lifecycle. Deterministic.

**Alternatives rejected**: a fixed neutral status — less informative; the
roll-up is cheap and honest.

## D4 — Adapter: `suite_id` → `scope.task_id`, backward compatible

**Decision**: `assembly_item_*` and `file_diff` set `scope.task_id` to
`payload.suite_id` when present (else leave unset), keep `work_item_id` as
`scope.work_item_id`. With D2, items then nest under the suite.

**Why**: IF 0.9.13 provides the parent; one-field pass-through is all that's
needed. Guarding on presence keeps older IF streams working (fall back to
"unassigned"), satisfying FR-009.

**Alternatives rejected**: require `suite_id` — breaks pre-0.9.13 streams.

## D5 — No DiffViewer / no new event types

**Decision**: no rendering-layer change. `DiffView.files`/`bodies` already list
multiple files (the widget renders a changed-file list); accumulation simply
populates more of them. No new canonical event types — `diff_ready` gains an
**optional** `reset` payload key, not a new type.

**Why**: smallest change that delivers the outcome; keeps the contract stable.

## D6 — Redaction over-reach on deep relative paths (found mid-implementation)

**Finding**: Rendering the real IF run crashed the `DiffViewer` with
`DuplicateIds`. Root cause: the public-safe redactor's `_POSIX_PATH` matched the
*interior* of deep **relative** repo paths (`src/integration_workbench/api.py` →
`src‹redacted›`), collapsing many distinct files to one display string — which
collided both as widget IDs and in `DiffView.bodies` (keyed by path). Shallow
relative paths (`src/app.py`) already survived (the regex needs ≥2 segments), so
this was latent until a real multi-file, deep-path run hit it.

**Decision**: (1) Tighten `_POSIX_PATH` to only match **absolute** POSIX paths —
the leading `/` must not follow a word char (`(?<!\w)`), so relative repo paths
survive (they aren't sensitive and are exactly what a diff view shows).
(2) Defensively key `DiffViewer` list items by **index**, not path, so any
future genuine path collision (a path that truly redacts) can't duplicate widget
IDs.

**Why**: relative paths are not secrets; over-redacting them made the multi-file
diff useless under the default public-safe mode (the whole point of this
feature). Absolute paths (`/home/…`, `C:\…`) and tokens/URLs stay redacted.

**Alternatives rejected**: key `DiffView.bodies` by index too — larger change;
fixing redaction makes paths distinct so bodies key cleanly, and the index-based
widget IDs already remove the crash class.

## Open questions / deferred

- **Activity strip on assembly-only streams**: no run/suite lifecycle event
  exists there, so the strip stays idle; driving it (e.g. work_item_started →
  thinking) is deferred to a separate slice.
- **Per-file diff selection UX** (scrolling among many files): the widget
  already supports a file list; richer navigation is out of scope.
