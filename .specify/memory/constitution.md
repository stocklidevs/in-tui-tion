<!--
Sync Impact Report
==================
Version change: (template) → 1.0.0
Rationale: Initial ratification of the project constitution.

Modified principles: n/a (initial adoption)
Added sections:
  - Core Principles (7 principles)
  - Technology & Platform Constraints
  - Development Workflow & Quality Gates
  - Governance
Removed sections: none

Templates reviewed:
  - .specify/templates/plan-template.md ✅ aligned (generic Constitution Check
    gate resolves against this file; no edits required)
  - .specify/templates/spec-template.md ✅ aligned (no constitution-specific
    mandatory sections introduced)
  - .specify/templates/tasks-template.md ✅ updated (tests for core logic are
    now REQUIRED per Principle VII, no longer optional)
  - AGENTS.md ✅ aligned (generic pointer to current plan; no agent-specific
    references requiring updates)

Follow-up TODOs: none
-->

# in-TUI-tion Constitution

in-TUI-tion is a generic Python TUI framework for agentic applications: a live
operator command center where users prompt for goals, review plans, steer
execution, watch parallel work, inspect diffs and evidence, and review history.
IntentForge is the first seed application, integrated through an adapter. See
`docs/ref/tui-user-requirements.md` for the full requirements baseline.

## Core Principles

### I. Structured State, Not Raw Logs

The TUI MUST render structured state derived from data, never raw log text.
All information flows through a single unidirectional contract:

```text
app adapter -> append-only event stream -> reducer/state store
  -> view models -> widgets -> user actions -> app adapter
```

Events are append-only facts with stable IDs, timestamps, types, and scopes.
Widgets MUST consume view models derived from reduced state; they MUST NOT
parse logs, read app files directly, or hold authoritative state of their own.

**Rationale**: A single event/state contract is what makes the framework
generic, replayable (live and historical views use the same pipeline), and
testable without a terminal.

### II. Generic Core, Adapters at the Edge

The core framework MUST contain no application-specific knowledge. Anything
specific to a host application (IntentForge included) MUST live in an adapter
that maps the app's events, state, artifacts, and actions into the common
contract. The core MUST be usable by a non-IntentForge application without
modification.

**Rationale**: IntentForge is the first demanding seed app, not the product.
Adapter-first keeps the framework reusable and prevents the host harness from
being forced to become a TUI runtime.

### III. Actions Are Intents

Every mutation of execution state (approve, reject, interrupt, cancel, retry,
rework, answer) MUST be expressed as a named, intentful action routed through
the host application's action API or adapter. The TUI MUST NOT perform ad hoc
file or process manipulation. Adapters MUST validate actions before execution,
and risky or destructive actions MUST require explicit confirmation.

**Rationale**: Intentful actions keep the TUI auditable and safe, and let each
host app enforce its own execution boundaries.

### IV. Keyboard-First, Accessible, Mouse-Friendly

All primary actions MUST be reachable by keyboard. Mouse interaction SHOULD be
supported wherever it is natural. Color MUST NOT be the only signal for any
status: every color-coded state needs a textual or symbolic counterpart.

**Rationale**: Operators live in terminals; accessibility and keyboard flow
are core product quality, not polish.

### V. Meaningful Motion

Visual effects MUST communicate state. The signature activity indicator (the
KITT-style swooshing light) and all other ambient signals MUST be data-driven
from the state store — red for thinking, amber for awaiting input, cyan for
verification, green for success, violet for history/comparison, fast red
strobe for failures. Decorative effects that carry no state meaning MUST NOT
be added.

**Rationale**: Eye candy is welcome when it carries meaning; otherwise it is
noise that erodes operator trust in the signals that do matter.

### VI. Public-Safe by Default

Views that render evidence or run data MUST respect public-safety boundaries:
provider endpoints, tokens, credentials, local absolute paths, and raw
provider configuration MUST NOT appear in public-safe views. Artifacts carry
an explicit `public_safe` flag, and renderers MUST honor it.

**Rationale**: IntentForge's evidence model depends on publishable run traces;
leaking one secret destroys that guarantee.

### VII. Test-First and Replayable

Core logic (event parsing, reducers, view models, adapters) MUST be developed
test-first: tests written and failing before implementation. Because of
Principle I, this logic MUST be testable headlessly by feeding recorded event
streams; every bug fix SHOULD add a replayable event fixture reproducing it.
Widget/visual behavior SHOULD be covered with the framework's snapshot or
pilot testing facilities where practical.

**Rationale**: A streaming UI is hard to debug live; replayable fixtures make
correctness cheap to verify and regressions cheap to catch.

## Technology & Platform Constraints

- Language: Python (modern, actively supported versions).
- The framework MUST run on common modern terminals on Windows, macOS, Linux,
  and WSL. Features that cannot work on all supported platforms MUST degrade
  gracefully rather than crash.
- The TUI MUST remain responsive while long-running work streams events;
  event ingestion and rendering MUST NOT block the UI loop.
- The common event schema MUST be versioned (a `version` field in the event
  envelope) from the first release; schema changes follow the same semantic
  versioning discipline as this constitution.
- New runtime dependencies require justification in the plan's Constitution
  Check; prefer the chosen TUI toolkit's built-ins over additional packages.

## Development Workflow & Quality Gates

- All feature work follows the Spec Kit flow: specify → clarify → plan →
  tasks → implement, on a feature branch.
- The plan's Constitution Check gate MUST pass before Phase 0 research and be
  re-checked after Phase 1 design; violations MUST be justified in Complexity
  Tracking or the design simplified.
- Tests MUST pass before a feature is considered complete; reducers, adapters,
  and view models MUST NOT merge without headless tests (Principle VII).
- Code review (human or agent) MUST verify compliance with this constitution,
  especially adapter boundaries (Principle II) and public-safety (Principle VI).
- Start simple (YAGNI): MVP scope is a read-mostly TUI replaying one run;
  process control, file editing, and plugin systems come later and need their
  own specs.

## Governance

This constitution supersedes other development practices for this repository.
Where a spec, plan, or implementation conflicts with it, the constitution
wins until formally amended.

- **Amendments**: proposed as a PR modifying this file, including a Sync
  Impact Report and updates to any dependent templates in
  `.specify/templates/`. Approval by the project maintainer ratifies the
  amendment.
- **Versioning**: semantic versioning of this document. MAJOR for removals or
  incompatible redefinitions of principles, MINOR for new principles or
  materially expanded guidance, PATCH for clarifications and wording.
- **Compliance review**: every plan re-validates against the current version;
  reviews of PRs MUST flag violations. Justified exceptions live in the
  plan's Complexity Tracking table, never silently.

**Version**: 1.0.0 | **Ratified**: 2026-06-12 | **Last Amended**: 2026-06-12
