# Feature Specification: Stream Contract & Packaging

**Feature Branch**: `008-stream-contract-packaging`

**Created**: 2026-06-13

**Status**: Draft

**Input**: User description: "Canonical event-stream contract and packaging: a documented emit-JSON-get-a-console vocabulary with a JSON Schema and an engine-free validator, plus pip-installable packaging (metadata, py.typed, buildable wheel) and an author quickstart guide"

## Overview

The on-ramp milestone. Today in-TUI-tion is powerful but hard to adopt: the
event vocabulary is spread across feature docs, there's no single "emit these
JSON lines and you get a console" contract a producer can target, no way to
validate a stream, and the library isn't installable (`pip install`) with a
typed, documented surface.

This feature makes the library **targetable and installable**:

1. A **canonical event-stream contract** — one consolidated, documented
   vocabulary (the event types and payload conventions our reducers consume),
   a JSON Schema, and an engine-free **validator** a producer can run to check
   a stream before pointing a console at it.
2. **Packaging** — enriched distribution metadata, a `py.typed` marker, a
   buildable/installable wheel, and a verified clean install.
3. An **author quickstart guide** — "emit JSON, get a console" and "build your
   own console" so a newcomer goes from zero to a running console fast.

This is deliberately the step *before* the zero-config runner and the
IntentForge adapter: both will target this stable, documented, installable
contract. It does not add new runtime UI components.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Target the canonical stream contract (Priority: P1)

A developer building any producer (an agent, a CI job, a data pipeline, the
IntentForge adapter) reads one document that lists the event types and payload
conventions, and emits JSONL lines that conform. They can validate a sample
stream against the contract and get clear, actionable errors before wiring a
console.

**Why this priority**: The contract is the product's public promise — "emit
these lines, get a console." Without it, every producer reverse-engineers the
vocabulary from feature docs. It's the smallest complete unit of adoptability.

**Independent Test**: Run the validator over a conforming sample stream (passes)
and a malformed one (reports each problem with line number and reason), all
headlessly.

**Acceptance Scenarios**:

1. **Given** the contract document and JSON Schema, **When** a developer reads
   it, **Then** every event type a console reduces is listed with its required
   envelope fields and payload conventions.
2. **Given** a conforming JSONL stream, **When** validated, **Then** the
   validator reports success.
3. **Given** a stream with a malformed envelope (missing required field, bad
   timestamp, unknown envelope version), **When** validated, **Then** each
   problem is reported with the line number and a human-readable reason.
4. **Given** an event whose `type` is outside the canonical vocabulary, **When**
   validated, **Then** it is reported as a *warning* (unknown types are allowed
   to pass through at runtime), not a hard error.
5. **Given** the JSON Schema, **When** used by an external tool, **Then** it
   validates the envelope shape independently of Python.

---

### User Story 2 - Install and import the library (Priority: P1)

A developer runs `pip install in-tui-tion` (from a built wheel), imports
`intui`, and gets a typed, documented package — type checkers see the inline
types, and the public API is what the contract documents.

**Why this priority**: "Super simple to use" starts with being installable.
Today the only way to use it is to vendor the source.

**Independent Test**: Build the wheel, install it into a clean environment,
import `intui` and the kit, and verify the version and a representative public
symbol are importable; verify the `py.typed` marker ships in the wheel.

**Acceptance Scenarios**:

1. **Given** the project, **When** a wheel is built, **Then** it builds without
   error and contains the `intui` package and its `py.typed` marker.
2. **Given** the built wheel, **When** installed into a clean environment,
   **Then** `import intui` works and `intui.__version__` matches the package
   version.
3. **Given** the installed package, **When** a type checker runs against code
   that uses it, **Then** the inline types are seen (the package is typed).
4. **Given** the distribution metadata, **When** inspected, **Then** it carries
   a description, author, license, homepage/repository URLs, keywords, and
   classifiers suitable for a public release.

---

### User Story 3 - Go from zero to a console with the guide (Priority: P2)

A newcomer follows a single quickstart that shows the two paths — "emit JSON
lines and point a console at them" and "build a console in code" — and reaches
a running example quickly, with the contract and public API linked.

**Why this priority**: Documentation is the difference between a capable library
and an adoptable one (the market research flagged docs/onboarding as a top
pain). It depends on the contract (US1) and install (US2) being settled.

**Independent Test**: Follow the quickstart steps from a fresh checkout/clean
install and reach a running example using only documented commands.

**Acceptance Scenarios**:

1. **Given** the quickstart, **When** followed from a clean install, **Then**
   the reader reaches a running example via documented steps only.
2. **Given** the guide, **When** read, **Then** it covers both the stream-first
   path and the build-in-code path and links the contract + public API.
3. **Given** the docs, **When** a reader wants the event vocabulary, **Then**
   the contract document is the single source of truth (feature docs link to
   it, not duplicate it).

---

### Edge Cases

- A JSONL stream with blank lines or a trailing newline: tolerated by the
  validator (blank lines skipped), consistent with the recording reader.
- A stream whose final line is a non-event record (e.g. a producer's summary
  line): the validator can be told which record types are events vs. ignorable.
- Envelope schema version drift: the validator reports an unsupported envelope
  `version` as a hard error (forward-compat is explicit, not silent).
- Very large streams: validation is streaming/line-by-line, not whole-file in
  memory.
- The contract must not duplicate per-feature payload schemas to the point of
  drift — it references the kit's documented conventions; a test guards that the
  canonical type list matches what the reducers actually handle.

## Requirements *(mandatory)*

### Functional Requirements

**Canonical contract**

- **FR-001**: The system MUST provide a single canonical document enumerating
  the event-stream vocabulary: every event `type` a bundled reducer consumes,
  its required envelope fields, and its payload conventions.
- **FR-002**: The system MUST publish a JSON Schema for the event envelope
  (extending the existing schema) usable by non-Python tools.
- **FR-003**: The system MUST provide an engine-free validator that checks a
  JSONL stream and reports, per line, envelope problems (hard errors) and
  unknown-type usage (warnings), each with line number and reason.
- **FR-004**: The canonical vocabulary MUST be exposed programmatically (a
  stable set/registry of known event types) so producers and tests can
  reference it rather than hard-coding strings.
- **FR-005**: A test MUST guard that the canonical type registry stays in sync
  with the event types the bundled reducers actually handle (no drift).

**Packaging**

- **FR-006**: The package MUST build into a wheel containing `intui` and a
  `py.typed` marker (PEP 561), with no source-only assumptions.
- **FR-007**: The distribution metadata MUST include description, author,
  license, project URLs (homepage/repository), keywords, and trove classifiers
  appropriate for a public release; `requires-python` MUST match the supported
  versions.
- **FR-008**: `intui.__version__` MUST equal the distribution version, with a
  single source of truth (no divergent version strings).
- **FR-009**: The built wheel MUST install into a clean environment and
  `import intui` (and the kit) MUST succeed without the repo checkout.

**Guide**

- **FR-010**: The system MUST provide an author quickstart covering the
  stream-first path ("emit JSON → get a console") and the build-in-code path,
  linking the contract and the public API.
- **FR-011**: Existing feature/example docs MUST link to the canonical contract
  rather than re-document the vocabulary (single source of truth).

**Cross-cutting**

- **FR-012**: The validator and contract registry MUST be engine-free and
  headlessly testable (Principle VII), consistent with the layering guard.
- **FR-013**: The contract MUST preserve public-safety guidance — it documents
  that payloads may carry a public-safety flag and that evidence/diff renderers
  redact by default (Principle VI).

### Key Entities

- **Event vocabulary registry**: the canonical, programmatic set of known event
  `type` values the bundled reducers consume (task/work-item/lane, artifacts,
  conversation, modes, views, run/gate, activity).
- **Envelope JSON Schema**: the published schema for the event envelope.
- **Stream validator**: an engine-free function reporting per-line errors and
  warnings for a JSONL stream.
- **Distribution metadata**: the `pyproject` project table + `py.typed` marker
  defining the installable, typed package.
- **Author quickstart**: the onboarding document for both adoption paths.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A producer can validate a conforming stream and get success, and a
  malformed stream and get a per-line problem list — verified headlessly.
- **SC-002**: The canonical type registry matches the bundled reducers' handled
  types exactly (drift test passes).
- **SC-003**: A wheel builds and installs into a clean environment; `import
  intui` works and `intui.__version__` equals the distribution version.
- **SC-004**: The package is typed — a type checker sees inline types via the
  shipped `py.typed`.
- **SC-005**: A newcomer reaches a running example from the quickstart using
  only documented steps (validated against a clean install/checkout).
- **SC-006**: The JSON Schema validates the envelope shape via a standard
  JSON-Schema validator (language-agnostic).

## Assumptions

- The distribution name is `in-tui-tion`; the import package is `intui` (already
  set); this feature formalizes metadata, it does not rename anything.
- Publishing to a public index (the actual upload) is out of scope; the
  deliverable is a build-and-install-verified wheel and release-ready metadata.
- The canonical vocabulary is the union of event types the *bundled* reducers
  handle; applications may still emit and reduce their own custom types (the
  validator treats unknown types as warnings, matching runtime tolerance).
- Per-type payload JSON Schemas (strict, per event type) are out of scope; the
  contract documents payload conventions and the schema validates the envelope.
  Strict per-type schemas can come later if producers ask for them.
- The zero-config console runner and the IntentForge adapter are the *next*
  features; they target this contract and are out of scope here.
