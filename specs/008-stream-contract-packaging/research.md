# Phase 0 Research: Stream Contract & Packaging

**Feature**: `008-stream-contract-packaging` | **Date**: 2026-06-13

Mostly consolidation + packaging; few true unknowns. Decisions below.

## R1. Vocabulary registry = union of per-reducer declared type sets (engine-free)

**Decision**: Each bundled state module declares the event types it handles as a
public module constant, the reducer *uses* that constant, and the canonical
registry is their union:

- `kit.state.reduce` → `TASKBOARD_EVENT_TYPES` (task_created/started/completed/
  blocked, work_item_started/completed, subagent_started/activity/completed)
- `kit.state.artifacts` → `ARTIFACT_EVENT_TYPES` (diff_ready, evidence_ready)
- `kit.state.conversation` → `CONVERSATION_EVENT_TYPES` (message_added,
  question_requested, approval_requested)
- `kit.state.modes` → `MODE_EVENT_TYPES` (mode_changed)
- `kit.state.views` → `VIEW_EVENT_TYPES` (view_selected)
- `kit.state` → `KNOWN_EVENT_TYPES = frozenset(union of the above)`

**Rationale**: Because each reducer *references its own constant*, the registry
cannot drift from what is actually handled (FR-005) — drift is structurally
impossible, not just tested. The registry lives in the kit (layer 2) where these
reducers live, keeping the foundation free of app vocabulary.

**Alternatives considered**: a hand-maintained list in the foundation (drifts,
and inverts the layer dependency); source-parsing the reducers (fragile).

## R2. Validator in the foundation, generic; vocabulary injected

**Decision**: `intui.events` gains an engine-free `validate_event(data, *,
known_types=None)` and `validate_stream(lines, *, known_types=None,
event_types=("run_trace_event",)?)` returning a list of `StreamIssue`
(line number, severity error|warning, reason). Envelope problems reuse
`parse_event`/`EnvelopeError` (hard errors); a `type` outside `known_types`
(when provided) is a warning. The kit passes `KNOWN_EVENT_TYPES`.

**Rationale**: Envelope validation is a foundation concern (the envelope is
foundation); the vocabulary is injected so the foundation stays vocabulary-free.
Unknown types are warnings, matching the runtime reducer contract (unknown types
pass through).

## R3. Published JSON Schema = the canonical envelope schema in docs/

**Decision**: Promote the envelope JSON Schema to `docs/contracts/
event-envelope.schema.json` (canonical, repo-level), referenced by the contract
doc and verified in tests with a standard JSON-Schema check. The per-feature
copy in `specs/001-…` stays as historical; docs/ is the published one.

**Rationale**: A repo-root `docs/contracts/` path is the obvious place external
tools look; keeps the published artifact separate from spec history.
`jsonschema` is added as a **dev-only** dependency for the verification test
(not a runtime dep — our own validator is hand-rolled and dependency-free).

## R4. Single-source version via hatchling dynamic version

**Decision**: `src/intui/__init__.py` `__version__` is the single source;
`pyproject` declares `dynamic = ["version"]` with
`[tool.hatch.version] path = "src/intui/__init__.py"`. Bump the version to a
pre-1.0 release number (e.g. `0.8.0`, matching the feature count milestone).

**Rationale**: One version string (FR-008). Hatchling natively reads
`__version__` from a module — no extra tooling.

## R5. py.typed + metadata

**Decision**: Add `src/intui/py.typed` (PEP 561); hatchling ships package files
so it's included. Enrich `[project]`: authors, `license`, `keywords`,
`classifiers` (Python 3.11–3.13, Topic :: Terminals, Typing :: Typed,
Environment :: Console, License), and `[project.urls]` (Homepage, Repository).
Verify the wheel builds (`uv build`) and installs into a throwaway env with
`import intui` + `intui.__version__`.

**Rationale**: Standard PEP 561 + release-ready metadata (FR-006/007/009). The
clean-install check is the real proof, run in CI-style as a scripted step.

## R6. Docs = one contract + one quickstart, feature docs link in

**Decision**: `docs/event-stream-contract.md` (the single vocabulary source) and
`docs/quickstart.md` (stream-first path + build-in-code path). Update the root
README and the per-feature/example READMEs to *link* the contract rather than
restate the vocabulary (FR-011).

**Rationale**: One source of truth prevents doc drift; the quickstart is the
adoption funnel the market research said we lack.
