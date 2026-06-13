# Feature Specification: Inspect Components

**Feature Branch**: `004-inspect-components`

**Created**: 2026-06-13

**Status**: Draft

**Input**: User description: "Inspect components: a diff viewer (changed-file list plus green/red line diff) and an evidence summary panel, both data-driven from artifacts in the event stream with public-safety enforcement"

## Overview

The "inspect / review" half of the component kit (R8, R9): components for
looking at the work a run produced. A **diff viewer** shows the list of
changed files and, for the selected file, a green/red line diff. An **evidence
summary panel** shows a run's outcome metrics — pass rate, quality counts,
scores, failure categories, delivered files. Both are data-driven from
**artifacts** carried in the event stream, and both honor **public-safety**:
when a view is public-safe, provider endpoints, tokens, credentials, and local
absolute paths must never appear (Constitution Principle VI).

Like the rest of the kit, these are generic: a "diff" is any set of changed
files with line changes (code, config, generated text), and "evidence" is any
labeled set of outcome metrics. Applications emit artifact events; the kit
reduces them into an artifact store the components render. Diff parsing and
redaction are engine-free and headlessly testable.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Inspect changed files with the diff viewer (Priority: P1)

A reviewer opens the diff viewer, sees the list of files a run changed (each
with added/removed counts), selects a file with the keyboard, and reads its
diff with added lines marked green and removed lines marked red — additions and
removals also distinguished by a `+`/`-` marker, not color alone.

**Why this priority**: Diff inspection (R8) is the core review affordance and
the smallest complete inspect unit — a working changed-file list plus a
rendered diff is independently useful, and it establishes the artifact model
the evidence panel reuses.

**Independent Test**: Replay a run that emits a diff artifact, verify the
changed-file list matches the artifact, select a file, and verify its diff
renders with correct add/remove/context lines and per-file counts.

**Acceptance Scenarios**:

1. **Given** a run that produced a diff over several files, **When** the diff
   viewer renders, **Then** it lists each changed file with its added and
   removed line counts.
2. **Given** the file list, **When** the reviewer selects a file with the
   keyboard, **Then** that file's diff is shown with added, removed, and
   context lines each visibly distinct by marker (`+`/`-`/space) and color.
3. **Given** a selected file's diff, **When** it is rendered, **Then** added
   and removed lines are distinguishable with color disabled (the `+`/`-`
   marker remains).
4. **Given** a very large diff, **When** it is shown, **Then** the diff body
   scrolls and stays responsive rather than blocking or clipping.
5. **Given** a run with no changed files, **When** the viewer renders, **Then**
   it shows an explicit empty state.
6. **Given** a binary or unparseable file change, **When** it appears in the
   list, **Then** it is shown with an explicit "no text diff" placeholder
   rather than crashing.

---

### User Story 2 - Review outcomes with the evidence panel (Priority: P2)

A reviewer opens the evidence panel for a run and sees its outcome metrics —
pass rate, quality issue count, a score and level, operation counts, drift,
failure categories, and delivered files — laid out as labeled values, updating
if the run is still live.

**Why this priority**: Evidence browsing (R9) is what lets a reviewer decide
whether a run is trustworthy. It depends on the same artifact model US1
establishes but is independently testable.

**Independent Test**: Replay a run that emits an evidence artifact, verify each
metric renders with its label and value, and verify a live update to the
artifact updates the panel.

**Acceptance Scenarios**:

1. **Given** an evidence artifact with metrics, **When** the panel renders,
   **Then** each metric appears as a labeled value (pass rate, counts, score
   and level, drift, failure categories, delivered files).
2. **Given** a metric with a status meaning (e.g. pass/fail, score level),
   **When** it renders, **Then** its status is conveyed by label/symbol, not
   color alone.
3. **Given** the run updates its evidence while live, **When** a new evidence
   artifact arrives, **Then** the panel updates to the latest values without
   disturbing unrelated metrics.
4. **Given** an evidence artifact missing some metrics, **When** the panel
   renders, **Then** present metrics show and absent ones are omitted or shown
   as "n/a" rather than rendering blank or crashing.

---

### User Story 3 - Public-safe inspection (Priority: P1)

A reviewer views diffs and evidence in a public-safe context (e.g. shared
output). Unsafe details — provider endpoints, tokens, credentials, local
absolute paths, raw provider configuration — must not appear; they are redacted
or omitted, while the useful structure (which files changed, the metrics)
remains visible.

**Why this priority**: Public-safety is non-negotiable (Principle VI) and the
inspect components are exactly where evidence is rendered, so this is the
feature where enforcement becomes real — it ships with US1, not after.

**Independent Test**: Provide artifacts containing unsafe fields and absolute
paths, render both components in public-safe mode, and verify no unsafe value
appears in the output while safe structure remains.

**Acceptance Scenarios**:

1. **Given** an artifact flagged not public-safe (or fields marked unsafe),
   **When** rendered in public-safe mode, **Then** unsafe values are replaced
   with a redaction marker and never appear verbatim.
2. **Given** a diff whose file paths are local absolute paths, **When**
   rendered in public-safe mode, **Then** paths are shown relative/redacted
   with no absolute local prefix.
3. **Given** the same artifacts rendered with public-safe mode off (a trusted
   local context), **When** rendered, **Then** full values are shown.
4. **Given** an evidence metric whose value is unsafe, **When** rendered in
   public-safe mode, **Then** the metric's label still shows with a redaction
   marker in place of the value.

---

### Edge Cases

- A diff line that is neither add/remove/context (malformed hunk): tolerated,
  shown as context, never crashing.
- File paths with mixed separators (Windows/POSIX): normalized for display.
- Evidence values of varying types (numbers, percentages, lists): each
  rendered readably; lists (failure categories, delivered files) shown as
  enumerations.
- An artifact arriving before the component mounts, and multiple artifacts of
  the same type: the latest of each type wins; selection is preserved across
  updates where possible.
- Redaction must not be defeatable by formatting (e.g. an unsafe value
  embedded in a larger string is still redacted).
- Extremely long single diff lines: truncated for display rather than breaking
  layout.

## Requirements *(mandatory)*

### Functional Requirements

**Artifact model (shared)**

- **FR-001**: The kit MUST define an artifact model covering a diff artifact
  (a set of changed files, each with path, added/removed counts, and ordered
  diff lines tagged add/remove/context) and an evidence artifact (an ordered
  set of labeled metrics, including list-valued metrics), each carrying a
  public-safety flag.
- **FR-002**: The kit MUST provide a reduction from artifact events
  (`diff_ready`, `evidence_ready`) into an artifact store slice, keeping the
  latest artifact of each type, usable with the pipeline without custom
  reducers.
- **FR-003**: The kit MUST parse unified-diff text into the structured file/
  line model, engine-free and headlessly, tolerating malformed or binary
  entries without crashing.
- **FR-004**: Applications MUST be able to supply the structured artifacts
  directly (bypassing event reduction) and bind components to their own
  view models of the declared shapes.

**Diff viewer**

- **FR-005**: The diff viewer MUST render the changed-file list with per-file
  added/removed counts and an empty state when there are no changes.
- **FR-006**: The diff viewer MUST let the reviewer select a file by keyboard
  and show that file's diff with add/remove/context lines distinguished by
  both a `+`/`-`/space marker and theme color.
- **FR-007**: The diff body MUST scroll and remain responsive for large diffs,
  and MUST show a "no text diff" placeholder for binary/unparseable files.

**Evidence panel**

- **FR-008**: The evidence panel MUST render each metric as a labeled value,
  support list-valued metrics, and omit or mark absent metrics as "n/a"
  rather than blank.
- **FR-009**: Metric statuses MUST be conveyed with a label or symbol in
  addition to color (no color-only status).
- **FR-010**: The panel MUST update to the latest evidence artifact when a new
  one arrives, without disturbing unrelated metrics.

**Public-safety (cross-cutting, Principle VI)**

- **FR-011**: Both components MUST support a public-safe rendering mode in
  which values flagged unsafe — and recognizably unsafe content (provider
  endpoints, tokens, credentials, local absolute paths, raw provider config) —
  are replaced with a redaction marker and never rendered verbatim.
- **FR-012**: Redaction MUST be applied by the engine-free model layer (so it
  is headlessly testable) and MUST NOT be defeatable by surrounding formatting.
- **FR-013**: With public-safe mode off, full values MUST render (trusted
  local context); the default mode MUST be public-safe.

**Cross-cutting**

- **FR-014**: Both components MUST re-render only when their bound view model
  changes and stay responsive under streaming updates.
- **FR-015**: Both components MUST be fully keyboard-operable with visible
  focus; no information may depend on color alone (Principle IV).
- **FR-016**: The feature MUST extend the examples gallery so a runnable
  example demonstrates the diff viewer and evidence panel over a recorded run,
  including a public-safe rendering (Principle VIII).

### Key Entities

- **FileDiff**: path (display + raw), added count, removed count, ordered
  `DiffLine`s, a "no text diff" flag for binary/unparseable entries.
- **DiffLine**: kind (add | remove | context), text, optional line numbers.
- **DiffArtifact**: id, title, ordered FileDiffs, public-safety flag.
- **EvidenceMetric**: key, label, value (scalar or list), optional status,
  unsafe flag.
- **EvidenceArtifact**: id, title, ordered EvidenceMetrics, public-safety flag.
- **ArtifactStore**: derived slice holding the latest diff and evidence
  artifacts; produced by the reduction or supplied by the application.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For a replayed run with a known diff, the changed-file list and
  per-file add/remove counts match the artifact exactly (verified headlessly).
- **SC-002**: A reviewer can select any changed file by keyboard and see its
  diff; 100% of diff navigation is keyboard-operable with visible focus.
- **SC-003**: In public-safe mode, no unsafe value (token, endpoint,
  credential, absolute local path) from a crafted artifact appears anywhere in
  rendered output (verified headlessly across both components).
- **SC-004**: With color disabled, additions and removals in a diff, and
  pass/fail statuses in evidence, remain distinguishable.
- **SC-005**: A new evidence artifact arriving for a live run updates the
  panel to the new values within one render frame.
- **SC-006**: All model behavior (diff parsing, reduction, redaction, metric
  projection) is verified by headless tests with recorded fixtures — zero
  terminal-dependent tests for model logic.

## Assumptions

- Diff input is unified-diff text or already-structured FileDiffs; side-by-side
  diff layout and inline intra-line highlighting are out of scope (later).
- Evidence metric set is open; the example uses an IntentForge-flavored set
  (pass rate, ACB score/level, quality issues, drift, failure categories,
  delivered files) but the panel is agnostic to which metrics exist.
- Public-safety detection combines explicit unsafe flags on artifacts/fields
  with a built-in redactor for well-known unsafe patterns (absolute paths,
  token-like strings, URLs with credentials); the redactor is conservative and
  extensible.
- Editing files or applying/reverting diffs is out of scope — inspection is
  read-only (R8 notes initial file exploration is read-oriented).
- The example may extend `mission_control` or add a new gallery entry — plan
  decision; either satisfies FR-016.
