# Research & Decisions: IntentForge Adapter

**Feature**: `010-intentforge-adapter` | **Date**: 2026-06-14

Each decision records what was chosen, why, and the alternatives rejected. The
IF event shapes were re-verified against the IF repo on 2026-06-14 (see D0).

## D0 — IF on-the-wire shape (verified, not assumed)

**Finding**: `intentforge … --event-stream ndjson` (the assembly-benchmark path,
`cli.py:_assembly_event_sink`) prints one line per event:
`{"type":"run_trace_event","event":{"sequence":N,"name":"<slug>","payload":{…}}}`
and a final `{"type":"summary","summary":{…}}` (`_write_stream_summary`). The
inner `event` is `RunTraceEvent.to_summary_dict()` — **not** an intui envelope.
Payload keys are the public-safe set (`run_trace.py:_PUBLIC_PAYLOAD_KEYS`):
`additions, case_id, change_type, deletions, diff, duration_ms,
execution_boundary, file, index, repeat_count, run_index, status, suite_id,
total, transaction_id, truncated, work_item_id`. Event names:
`case_started/finished`, `assembly_item_started/committed/failed`,
`assembly_plan_blocked`, `file_diff`, `matrix_suite_started/finished`,
`repeat_started/finished`. `file_diff` payload (`file_diff.py:to_dict`):
`file, change_type, additions, deletions, diff, truncated`. Assembly-item events
put the item id in **`case_id`** (and `file_diff` sets `case_id == work_item_id`).

**Why it matters**: confirms the adapter must *transform* records into envelopes
(can't just unwrap), drives the mapping table, and tells us assembly items carry
their id in `case_id` (D6).

## D1 — A pure `adapt_record` + a thin `IntentForgeSource`, in `intui.adapters`

**Decision**: The normalizer core is a pure function
`adapt_record(record, *, run_id) -> Event | None`; an `IntentForgeSource`
wraps it onto a stream. Both live in a new **engine-free** `intui.adapters`
subpackage (`intui.adapters.intentforge`).

**Why**: A pure function is trivially unit-testable per IF event and reusable by
others embedding IF normalization. A dedicated `intui.adapters` package signals
that producer adapters are first-class and gives future adapters a layering-
guarded home. Engine-free keeps the adapter testable without a terminal and
lets `watch()` consume it like any source.

**Alternatives rejected**: (a) bake IF handling into `NdjsonStreamSource` —
pollutes the generic source with producer specifics. (b) put it in
`intui.console` — that's the rendering layer; the adapter is pure logic and
belongs below it. (c) a Textual widget — wrong layer entirely.

## D2 — Deterministic synthetic timestamp from `sequence`

**Decision**: IF events carry no timestamp. The adapter synthesizes
`timestamp = EPOCH + timedelta(seconds=sequence)` (a fixed UTC epoch constant),
giving a valid, monotonic, **deterministic** timestamp.

**Why**: The envelope requires a parseable timestamp; replays must stay
deterministic (Principle VII). Wall-clock `now()` would make the same recording
reduce differently each run and break golden tests. `sequence` is monotonic and
unique within a run.

**Alternatives rejected**: (a) `datetime.now()` — non-deterministic. (b) require
the caller to supply timestamps — pushes work onto every consumer for no gain.

## D3 — Stable `event_id` from `sequence`; summary id is fixed

**Decision**: `event_id = f"if-{sequence}"` for run-trace events;
`event_id = "if-summary"` for the summary. `run_id` is supplied by the source
(default `"intentforge"`, overridable).

**Why**: Deterministic and unique within a run, so the store's dedupe behaves and
recordings are stable. The summary is singular per run, so a fixed id is fine.

**Alternatives rejected**: random UUIDs — non-deterministic, defeats replay
goldens.

## D4 — `IntentForgeSource` reads raw lines and dispatches (keeps the summary)

**Decision**: `IntentForgeSource` reads raw ndjson lines itself
(file/str/iterable/async-iterable, or a spawned command), `json.loads` each, and
calls `adapt_record` — so it sees **both** the `run_trace_event` wrappers **and**
the trailing `summary`. Malformed lines surface via the same `{"__malformed__"}`
marker as 009 (store records them in health).

**Why**: If we reused `NdjsonStreamSource(event_record_types=("run_trace_event",))`
it would drop the `summary` line (no `event_id`/not a wrapper) before the adapter
could map it to evidence. Reading raw lines keeps the summary. We still reuse
009's `_aiter_text_lines` and the extracted subprocess line helper, so there's no
duplicated I/O.

**Alternatives rejected**: (a) layer the adapter on top of `NdjsonStreamSource` —
loses the summary (the most valuable single record). (b) special-case the summary
in `NdjsonStreamSource` — leaks IF specifics into the generic source.

## D5 — Refactor: extract `_aiter_subprocess_lines` (shared by both sources)

**Decision**: Pull `SubprocessSource`'s spawn+stdout-line-read loop into a module
helper `_aiter_subprocess_lines(cmd) -> AsyncIterator[str]`; `SubprocessSource`
decodes those lines to envelopes (unchanged behavior), and `IntentForgeSource`
reuses the same helper for its live form.

**Why**: DRY — one place that spawns and reads stdout lines, two decoders on top.
No behavior change to `SubprocessSource` (covered by existing 009 tests).

**Alternatives rejected**: duplicate the spawn loop in `IntentForgeSource` —
drift risk, two places to fix Windows/asyncio quirks.

## D6 — Assembly-item id from `work_item_id` then `case_id`; parent left unassigned

**Decision**: For `assembly_item_*` and `file_diff`, the adapter reads the entity
id from `work_item_id` if present, else `case_id` (IF puts the item id in
`case_id`). Work items are emitted with `scope.work_item_id` set and **no**
`scope.task_id` (the IF event doesn't carry the parent case), so they land under
the kit's "unassigned" lane.

**Why**: Matches the verified IF shape; emitting work items without a fabricated
parent is honest (we don't invent linkage). The kit already handles unassigned
work items.

**Alternatives rejected**: (a) guess the parent from the most recent
`case_started` — stateful, fragile, and `adapt_record` is intentionally pure
(stateless per record). (b) drop work items — loses the assembly detail that is
core to an IF run.

## D7 — Summary → evidence: map recognized top-level metrics, ignore the rest

**Decision**: `summary` → `evidence_ready` with metrics built from the recognized
top-level keys of the summary payload (e.g. `case_pass_rate`,
`quality_issue_count`, plus `acb_score.certified_level` when present), each a
`{key,label,value}` metric. Unknown/nested/missing keys are ignored.

**Why**: The summary payload shape varies by IF subcommand; mapping a curated set
of stable top-level metrics gives a useful evidence panel without coupling to the
full nested structure or crashing on absence (FR-004). Values are strings/numbers
already public-safe per IF.

**Alternatives rejected**: (a) dump the entire summary as metrics — noisy, fragile
to shape changes, risks surfacing non-public nested data. (b) skip the summary —
loses the headline evidence (pass rate, certification) that justifies the panel.

## D8 — CLI `--adapter {none,intentforge}` (default none)

**Decision**: Add `--adapter` to `intui watch`; `none` (default) keeps 009
behavior, `intentforge` wraps the chosen input (file or `-- <cmd>`) in
`IntentForgeSource`. Extensible to future adapters by name.

**Why**: One discoverable switch covers both replay and live forms; default
`none` preserves the canonical-stream path. A named enum leaves room for more
producers without new flags.

**Alternatives rejected**: (a) a separate `intui watch-intentforge` subcommand —
duplicates option parsing. (b) auto-detect the IF shape — magic; explicit is
clearer and avoids misclassifying lookalike streams.

## Open questions / deferred

- **Richer summary metrics / nested ACB breakdown**: deferred; map the curated
  top-level set first.
- **Parent linkage for assembly items**: deferred (would need a stateful adapter
  or an IF event change to carry the parent case id).
- **Other IF subcommands**: covered for free if they emit the same record shape;
  no extra work planned here.
