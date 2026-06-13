# Implementation Plan: Inspect Components

**Branch**: `004-inspect-components` | **Date**: 2026-06-13 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/004-inspect-components/spec.md`

## Summary

The inspect/review kit slice (R8, R9): an engine-free artifact model
(`FileDiff`/`DiffArtifact`, `EvidenceMetric`/`EvidenceArtifact`,
`ArtifactStore`) with a unified-diff parser, a conservative redactor, an
`artifacts_slice()` reduction of `diff_ready`/`evidence_ready`, and
`diff_view`/`evidence_view` selectors that redact by default. Two Textual
components — `DiffViewer` (changed-file list + green/red diff body) and
`EvidencePanel` (labeled metric rows) — plus example wiring including a
public-safe rendering. Decisions in [research.md](research.md); model in
[data-model.md](data-model.md).

## Technical Context

**Language/Version**: Python 3.11–3.13 (unchanged)

**Primary Dependencies**: Textual 6.x (present). **No new runtime deps** —
diff parser and redactor are in-house (research R5).

**Storage**: JSONL recordings (unchanged).

**Testing**: pytest headless for `kit.state.artifacts` (parser, reduction,
redaction, selectors — incl. crafted unsafe inputs for SC-003); Pilot for the
two components; recorded fixtures.

**Target Platform**: unchanged (Windows/macOS/Linux/WSL terminals).

**Project Type**: library + examples gallery (unchanged).

**Performance Goals**: components re-render only on view change (FR-014); large
diffs scroll without blocking (FR-007); evidence updates within a frame (SC-005).

**Constraints**: `kit.state.artifacts` engine-free (lint + guard); redaction in
the model layer, default-on (Principle VI, FR-012/013); no color-only state
(FR-015).

**Scale/Scope**: artifact model + parser + redactor + 2 components + example.
Side-by-side diffs, intra-line highlighting, and file editing are out of scope.

## Constitution Check

| # | Principle | Status | Notes |
|---|-----------|--------|-------|
| I | Structured State | ✅ PASS | `diff_view`/`evidence_view` are selectors over the snapshot; artifacts reduced from events. |
| II | Layered Architecture | ✅ PASS | Model joins engine-free `kit.state` (guard + ban); components are layer-2 widgets on public APIs. |
| III | Actions Are Intents | ✅ PASS | Inspection is read-only; any future open/apply would route as intents. No state mutation. |
| IV | Keyboard-First, Accessible | ✅ PASS | File selection via engine list (visible focus); diff markers + evidence glyphs are non-color counterparts (SC-002/004). |
| V | Meaningful Motion | ✅ PASS (n/a) | No new motion. |
| VI | Public-Safe by Default | ✅ PASS (central) | Redaction in the pure model layer, default-on; SC-003 verified headlessly over crafted inputs. This feature is where VI is enforced. |
| VII | Test-First, Replayable | ✅ PASS | Parser/reduction/redaction/selectors headless test-first; components via Pilot. |
| VIII | Example-Driven | ✅ PASS | `mission_control` gains the diff viewer + evidence panel incl. a public-safe rendering (FR-016). |
| — | New deps justified | ✅ PASS | None — parser + redactor in-house (R5). |

**Post-Phase-1 re-check (2026-06-13)**: artifacts add no dependencies and hold
the layer boundary. GATE: PASS — Complexity Tracking empty.

## Project Structure

### Documentation (this feature)

```text
specs/004-inspect-components/
├── plan.md  research.md  data-model.md  quickstart.md
├── contracts/inspect-api.md
├── checklists/requirements.md
└── tasks.md (Phase 2 via /speckit-tasks)
```

### Source Code (repository root)

```text
src/intui/
├── kit/
│   ├── state/
│   │   └── artifacts.py     # ── engine-free ── artifact models, parse_unified_diff,
│   │                        #   redact, artifacts_slice, diff_view/evidence_view
│   ├── diff_viewer.py       # DiffViewer (BoundContainer)
│   └── evidence_panel.py    # EvidencePanel (BoundContainer)

tests/
├── unit/
│   ├── test_diff_parse.py       # unified-diff parser (headless)
│   ├── test_redact.py           # redactor incl. crafted unsafe inputs (SC-003)
│   └── test_artifacts.py        # reduction + diff_view/evidence_view selectors
└── snapshot/
    ├── test_diff_viewer.py      # file list, selection, green/red body, states
    └── test_evidence_panel.py   # metric rows, list values, status, n/a, update

examples/mission_control/        # add diff viewer + evidence panel + recording artifacts
```

**Structure Decision**: artifact model in engine-free `kit.state.artifacts`
(mirrors 002/003 `state` split); `DiffViewer` and `EvidencePanel` are
`BoundContainer`s; redaction lives in the pure layer so Principle VI is
headlessly provable.

## Complexity Tracking

No constitutional violations — table intentionally empty.
