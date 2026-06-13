# Tasks: Inspect Components

**Input**: Design documents from `/specs/004-inspect-components/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/inspect-api.md

**Tests**: Per Constitution Principle VII, tests for `intui.kit.state.artifacts` (parser, reduction, redaction, selectors) are REQUIRED and written first. Component behavior uses Pilot tests. Redaction (Principle VI) is verified headlessly over crafted unsafe inputs.

**Organization**: US1 (diff viewer) and US3 (public-safety) ship together; US2 (evidence panel) reuses the artifact model. The `mission_control` example gains both components.

## Format: `[ID] [P?] [Story] Description`

## Phase 1: Setup

- [X] T001 Add ruff per-file-ignores for `src/intui/kit/diff_viewer.py` and `src/intui/kit/evidence_panel.py` in `pyproject.toml` (kit.state stays banned; the layering guard already covers `intui.kit.state`)

## Phase 2: Foundational (artifact model + parser + redactor — blocks all stories)

- [X] T002 [P] Failing tests for the unified-diff parser in `tests/unit/test_diff_parse.py`: multi-file headers, hunk line numbers, add/remove/context classification + counts, `Binary files differ` → no_text_diff, malformed lines tolerated, mixed path separators normalized
- [X] T003 [P] Failing tests for the redactor in `tests/unit/test_redact.py` (SC-003): absolute Windows + POSIX paths, URLs with credentials, token-like strings (`sk-…`, long high-entropy), redaction of an unsafe substring inside a larger string, safe text left intact
- [X] T004 [P] Failing tests for artifact models in `tests/unit/test_artifacts.py`: frozen/value-equality of FileDiff/DiffArtifact/EvidenceMetric/EvidenceArtifact/ArtifactStore
- [X] T005 Implement `src/intui/kit/state/artifacts.py` part 1: models, `parse_unified_diff`, `redact`
- [X] T006 [P] Failing tests for the reduction + selectors in `tests/unit/test_artifacts.py`: `artifacts_slice` maps `diff_ready`/`evidence_ready` (structured + unified text), latest-of-type wins, unknown events pass through; `diff_view`/`evidence_view` shape, default public-safe redaction on, `public_safe=False` shows full, memoization/value-equality
- [X] T007 Implement `artifacts.py` part 2: `artifacts_slice`, `DiffView`/`EvidenceView` + `diff_view`/`evidence_view` (redaction default-on)
- [X] T008 Export the artifact model from `src/intui/kit/state/__init__.py` and add the components to the lazy exports in `src/intui/kit/__init__.py`
- [X] T009 Create committed fixture `tests/replay/fixtures/inspect_run.jsonl` (a `diff_ready` over several files incl. one binary + unsafe paths, an `evidence_ready` with scalar/list/status metrics incl. an unsafe value) and determinism test in `tests/replay/test_inspect_fixture.py`

**Checkpoint**: artifact model, parser, redactor, selectors complete and headlessly tested.

## Phase 3: User Story 1 + 3 — Diff viewer, public-safe (P1) [MVP]

- [ ] T010 [US1] Pilot tests (write first) in `tests/snapshot/test_diff_viewer.py`: changed-file list with counts, keyboard file selection updates the body, add/remove/context lines distinguishable by marker (color-disabled too), no_text_diff placeholder, empty state, selection preserved across stream update; public-safe default redacts absolute paths (US3), `public_safe=False` shows full
- [ ] T011 [US1] Implement `DiffViewer` in `src/intui/kit/diff_viewer.py` (BoundContainer: engine list for files + scrollable diff body; selection local state by path; marker+theme-color lines)
- [ ] T012 [US1] Add the `DiffViewer` to `examples/mission_control/app.py` + emit a `diff_ready` in the recording; verify `uv run python -m examples.mission_control`

**Checkpoint**: diff viewer inspectable; public-safe redaction visible.

## Phase 4: User Story 2 — Evidence panel (P2)

- [ ] T013 [US2] Pilot tests (write first) in `tests/snapshot/test_evidence_panel.py`: labeled metric rows, list-valued metric enumerates, status metric shows glyph+label (color-disabled identifiable), absent metric → n/a, latest evidence update refreshes without disturbing others, unsafe value redacted in public-safe mode
- [ ] T014 [US2] Implement `EvidencePanel` in `src/intui/kit/evidence_panel.py` (BoundContainer over `evidence_view`)
- [ ] T015 [US2] Add the `EvidencePanel` to `examples/mission_control/app.py` + emit an `evidence_ready` in the recording

**Checkpoint**: both inspect components live in the example.

## Phase 5: Polish & Cross-Cutting

- [ ] T016 [P] Extend the contract-drift test in `tests/unit/test_public_api.py` with the inspect-api.md names (`intui.kit.state` + `intui.kit`)
- [ ] T017 [P] Accessibility additions in `tests/snapshot/test_accessibility.py`: diff navigation keyboard-only (SC-002); add/remove + evidence statuses color-free identifiable (SC-004)
- [ ] T018 [P] Update `examples/mission_control/README.md` (diff viewer + evidence keys, public-safe note) and the root README kit list
- [ ] T019 Full gate: `uv run pytest && uv run ruff check && uv run mypy`; fix all findings; fresh-clone quickstart check

## Dependencies & Execution Order

```text
Setup -> Foundational (T002-T009) -> US1+US3 (MVP) -> US2 -> Polish
```

- Redaction (US3) is built into the Phase-2 selectors, so US1 ships public-safe
  from the first render; US2 reuses it.
- Within every phase: test tasks strictly before implementation (Principle VII).

## Implementation Strategy

MVP = Phases 1–3 (diff viewer, public-safe, in the example). Then the evidence
panel, then polish. The example grows per story (Principle VIII).
