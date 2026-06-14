# Tasks: Stream Contract & Packaging

**Input**: Design documents from `/specs/008-stream-contract-packaging/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/contract-api.md

**Tests**: Per Constitution Principle VII, tests for the validator, vocabulary registry/drift, version single-source, and the published JSON Schema are REQUIRED and written first.

**Organization**: US1 (contract + validator), US2 (packaging), US3 (docs/quickstart).

## Format: `[ID] [P?] [Story] Description`

## Phase 1: Setup

- [X] T001 Add `jsonschema` as a dev-only dependency in `pyproject.toml` (for the language-agnostic schema check); `uv sync`

## Phase 2: User Story 1 — Canonical contract + validator (P1) [MVP]

- [X] T002 [P] [US1] Failing tests for the vocabulary registry in `tests/unit/test_vocabulary.py`: each module exposes its `*_EVENT_TYPES`; `KNOWN_EVENT_TYPES` equals their union; drift guard — feeding one event of each declared type to the bundled reducers changes the corresponding slice (no stale declarations)
- [X] T003 [P] [US1] Failing tests for the validator in `tests/unit/test_validate.py`: `validate_event` clean pass, each envelope error (missing field, bad timestamp, unknown version) reported; unknown `type` → warning when `known_types` given; `validate_stream` per-line numbers, blank-line skip, JSON-parse error, `event_record_types` unwrapping (`{"type":"run_trace_event","event":{...}}`)
- [X] T004 [US1] Add `*_EVENT_TYPES` constants to `reduce.py`/`artifacts.py`/`conversation.py`/`modes.py`/`views.py` and make each reducer reference its constant; export them + `KNOWN_EVENT_TYPES` (union) from `kit/state/__init__.py`
- [X] T005 [US1] Implement `src/intui/events/validate.py` (`StreamIssue`, `validate_event`, `validate_stream`) and export from `intui.events`
- [X] T006 [US1] Publish `docs/contracts/event-envelope.schema.json` (canonical) + failing/then-passing `tests/unit/test_schema.py` validating sample envelopes via `jsonschema`
- [X] T007 [US1] Write `docs/event-stream-contract.md`: the canonical vocabulary table, payload conventions, recommended lifecycle conventions, public-safety guidance; link the schema

**Checkpoint**: a producer can read the contract and validate a stream headlessly.

## Phase 3: User Story 2 — Packaging (P1)

- [X] T008 [US2] Failing test for version single-source in `tests/unit/test_version.py`: `intui.__version__` equals `importlib.metadata.version("in-tui-tion")` (when installed) / matches the module source; one source only
- [X] T009 [US2] Switch `pyproject.toml` to dynamic version from `src/intui/__init__.py`; bump `__version__` to `0.8.0`; add `authors`, `keywords`, `classifiers`, `[project.urls]`; add `LICENSE` (MIT)
- [X] T010 [US2] Add `src/intui/py.typed` and ensure hatchling ships it in the wheel
- [X] T011 [US2] Build + clean-install verification: `uv build`, install the wheel into a throwaway env, assert `import intui`, `intui.__version__`, kit import, and `py.typed` present in the wheel; capture as a documented check (and a test that skips gracefully if no wheel)

**Checkpoint**: `pip install` works; package is typed; metadata is release-ready.

## Phase 4: User Story 3 — Author quickstart + doc consolidation (P2)

- [X] T012 [US3] Write `docs/quickstart.md`: stream-first path (emit JSON → validate → console-to-come) and build-in-code path (compose the kit, run an example), linking the contract + public API
- [X] T013 [P] [US3] Update root `README.md` and the example READMEs to link `docs/event-stream-contract.md` as the single vocabulary source (stop restating it); add an install section

**Checkpoint**: a newcomer can go from install to a running example via docs only.

## Phase 5: Polish & Cross-Cutting

- [X] T014 [P] Extend the contract-drift test in `tests/unit/test_public_api.py` with the new names (`validate_event`, `validate_stream`, `StreamIssue`, `KNOWN_EVENT_TYPES`)
- [X] T015 Full gate: `uv run pytest && uv run ruff check && uv run mypy`; fix all findings; fresh-clone quickstart check + wheel build/install

## Dependencies & Execution Order

```text
Setup -> US1 (contract+validator) -> US2 (packaging) -> US3 (docs) -> Polish
```

- US2 depends on US1 only for the version test location; US3 depends on US1+US2
  (docs link the contract + install). Within every phase: tests before
  implementation (Principle VII).

## Implementation Strategy

MVP = Phases 1–2 (contract + validator targetable). Then packaging (installable),
then docs (adoptable), then polish.
