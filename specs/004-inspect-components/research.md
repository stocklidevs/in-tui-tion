# Phase 0 Research: Inspect Components

**Feature**: `004-inspect-components` | **Date**: 2026-06-13

Platform decisions are settled (Textual engine, engine-free pipeline, kit
patterns from 002/003). This phase resolves only inspect-specific unknowns.

## R1. Artifact model + diff parser + redactor live in engine-free kit state

**Decision**: New engine-free module `intui/kit/state/artifacts.py` holding the
artifact dataclasses (`FileDiff`, `DiffLine`, `DiffArtifact`,
`EvidenceMetric`, `EvidenceArtifact`, `ArtifactStore`), the `artifacts_slice()`
reduction, the unified-diff parser, the redactor, and the `diff_view` /
`evidence_view` selectors. Joins the layering guard + ruff ban.

**Rationale**: Diff parsing, reduction, redaction, and metric projection are
all pure and must be headlessly testable (SC-006) and — for redaction —
provably correct without a terminal (SC-003, Principle VI). Same split as
002/003.

**Alternatives considered**: a separate top-level package (overkill); doing
redaction in the widgets (would make the most security-sensitive logic the
hardest to test — rejected).

## R2. Diff viewer: file list + diff body, master/detail in one BoundContainer

**Decision**: `DiffViewer(BoundContainer)` binds to `diff_view(...)`. Layout is
a changed-file list (left/top) and a scrollable diff body (the selected file).
The file list uses the engine's `ListView`/`OptionList` for keyboard selection
and visible focus; the diff body is a scrollable `Static` rendered from the
selected `FileDiff`. Selection (which file) is local UI state, preserved across
refreshes by file path (the research-R5 pattern from 002).

**Rationale**: Reuses engine widgets for navigation/scroll (constitution: lean
on built-ins); the kit owns the data direction (artifact → rows + diff text)
and selection persistence. One BoundContainer keeps the value-equality refresh
contract uniform.

**Alternatives considered**: Textual's `DataTable` for the diff body (rows are
not tabular — line markers + text suit a Static); two separate widgets wired by
the app (more glue; master/detail belongs in one component).

## R3. Diff body rendering via Rich Text with marker + theme color

**Decision**: Each `DiffLine` renders as `{marker}{text}` where marker is
`+`/`-`/space, colored from theme status tokens (`success` for add, `failure`
for remove, muted for context). The marker is the non-color counterpart
(SC-004). Long lines truncated to width.

**Rationale**: Marker-plus-color satisfies the no-color-only rule directly;
Rich Text styling is the same approach the Signal/kit components already use.

## R4. Evidence panel: labeled metric rows from a metric list

**Decision**: `EvidencePanel(BoundContainer)` binds to `evidence_view(...)`,
rendering each `EvidenceMetric` as a `label  value` row; list-valued metrics
render as an enumerated sub-block; status metrics get a glyph+label. Absent
metrics show `n/a`. Pure presentation; latest-artifact-wins from the store.

**Rationale**: Mirrors the chip/lanes row pattern; keeps the panel agnostic to
which metrics exist (FR-008).

## R5. Redaction: explicit flags + a conservative pattern redactor

**Decision**: `redact(text) -> str` and field/metric-level honoring of unsafe
flags, in `artifacts.py`. The pattern redactor targets: absolute local paths
(Windows `X:\…` and POSIX `/…`), URLs (esp. with credentials), and token-like
strings (long high-entropy / `sk-…`-style runs). Redaction replaces the match
with a `‹redacted›` marker in place (so an unsafe substring inside a larger
string is still removed — FR-012). The `diff_view`/`evidence_view` selectors
take a `public_safe: bool = True` parameter and apply redaction when on;
default is public-safe (FR-013).

**Rationale**: Defense in depth — explicit flags catch what the app knows,
the pattern redactor catches what it forgot. Doing it in the selector (pure)
makes SC-003 a headless test over crafted inputs. Default-on enforces
Principle VI by construction.

**Alternatives considered**: redact only on explicit flags (too easy to leak
by omission — Principle VI wants safe-by-default); a heavy PII/secret-scanning
dependency (overkill and a new runtime dep — the conservative in-house set is
enough and extensible).

## R6. Standard artifact event vocabulary

**Decision**: `diff_ready` (payload: `unified` text or structured `files`,
plus optional `public_safe`, `title`) and `evidence_ready` (payload: `metrics`
list of `{key,label,value,status?,unsafe?}`, plus `public_safe`, `title`).
Unknown event types pass through unchanged (foundation reducer contract).
Frozen in data-model.md.

**Rationale**: Matches the requirements doc's artifact envelope
(`artifact_id`, `type`, `title`, `public_safe`) and the existing NDJSON-ish
event shape; keeps apps emitting plain events with zero custom reducers.
