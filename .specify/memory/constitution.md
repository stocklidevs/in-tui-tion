<!--
Sync Impact Report
==================
Version change: 1.0.0 → 2.0.0
Rationale: MAJOR — the project identity is redefined from "a TUI framework for
agentic applications" to "a general-purpose library for building rich,
first-class TUIs", with the agentic operator console repositioned as the
flagship example. Principle II is materially redefined around a three-layer
architecture, and a new principle (VIII, Example-Driven) is added.

Modified principles:
  - Preamble: agentic-framework identity → library-first identity with
    three-layer architecture (core library / component kit / examples gallery)
  - II. Generic Core, Adapters at the Edge → II. Layered Architecture:
    Core, Components, Examples (redefined)
Added sections:
  - Principle VIII: Example-Driven
Removed sections: none

Templates reviewed:
  - .specify/templates/plan-template.md ✅ aligned (generic Constitution Check
    gate resolves against this file; no edits required)
  - .specify/templates/spec-template.md ✅ aligned
  - .specify/templates/tasks-template.md ✅ aligned (Principle VII reference
    unchanged; numbering preserved)
  - AGENTS.md ✅ aligned

Follow-up TODOs: none
-->

# in-TUI-tion Constitution

in-TUI-tion is a general-purpose Python library for building rich, modern,
first-class terminal user interfaces. It provides the foundations — a
state-driven component model, an event/reducer/view-model pipeline, theming,
and a data-driven motion system — plus a kit of high-level components, so that
any kind of TUI can be built with it.

Its most demanding showcase is an agentic operator console: a live command
center where users prompt for goals, approve plans, watch parallel work,
inspect diffs and evidence, and replay history. IntentForge is the first seed
application for that console, integrated through an adapter. The console is
the flagship *example*, not the product. See
`docs/ref/tui-user-requirements.md` for the console requirements baseline.

## Core Principles

### I. Structured State, Not Raw Logs

TUIs built with the library MUST render structured state derived from data,
never raw log text. All information flows through a single unidirectional
contract:

```text
app adapter -> append-only event stream -> reducer/state store
  -> view models -> widgets -> user actions -> app adapter
```

Events are append-only facts with stable IDs, timestamps, types, and scopes.
Widgets MUST consume view models derived from reduced state; they MUST NOT
parse logs, read app files directly, or hold authoritative state of their own.

**Rationale**: A single event/state contract is what makes the library
generic, replayable (live and historical views use the same pipeline), and
testable without a terminal.

### II. Layered Architecture: Core, Components, Examples

The project is organized in three strict layers:

1. **Core library**: general-purpose foundations — component model, event/
   reducer/view-model pipeline, theming, motion system, input handling.
2. **Component kit**: high-level reusable widgets (task chips, collapsible
   trees, parallel lanes, signal strips, diff viewers, evidence panels,
   approval prompts, command menus) built only on the core's public API.
3. **Examples and adapters**: runnable applications (the agentic operator
   console, IntentForge adapter, and smaller demos) built only on the public
   APIs of the layers below.

Dependencies point strictly downward. The core MUST contain no knowledge of
any specific application (IntentForge included); the component kit MUST be
framed generically (a "lane" can show CI jobs, not just subagents); anything
app-specific lives in an adapter or example.

**Rationale**: The library is the product. Strict layering is what keeps it
honest — usable for any TUI, not secretly single-purpose — while the demanding
flagship console drives real requirements into the lower layers.

### III. Actions Are Intents

Every mutation of application or execution state triggered from the UI
(approve, reject, interrupt, cancel, retry, rework, answer) MUST be expressed
as a named, intentful action routed through the host application's action API
or adapter. Library code MUST NOT perform ad hoc file or process manipulation.
Adapters MUST validate actions before execution, and risky or destructive
actions MUST require explicit confirmation.

**Rationale**: Intentful actions keep TUIs auditable and safe, and let each
host app enforce its own execution boundaries.

### IV. Keyboard-First, Accessible, Mouse-Friendly

All primary actions MUST be reachable by keyboard. Mouse interaction SHOULD be
supported wherever it is natural. Color MUST NOT be the only signal for any
status: every color-coded state needs a textual or symbolic counterpart.

**Rationale**: Operators live in terminals; accessibility and keyboard flow
are core product quality, not polish.

### V. Meaningful Motion

Visual effects MUST communicate state. The motion system, ambient indicators
(such as the KITT-style swooshing signal strip), and all other effects MUST be
data-driven from the state store — e.g., red for thinking, amber for awaiting
input, cyan for verification, green for success, violet for history/
comparison, fast red strobe for failures. Decorative effects that carry no
state meaning MUST NOT be added to the component kit.

**Rationale**: Eye candy is welcome when it carries meaning; otherwise it is
noise that erodes user trust in the signals that do matter.

### VI. Public-Safe by Default

Components that render evidence or run data MUST respect public-safety
boundaries: provider endpoints, tokens, credentials, local absolute paths, and
raw provider configuration MUST NOT appear in public-safe views. Artifacts
carry an explicit `public_safe` flag, and renderers MUST honor it.

**Rationale**: The flagship console's evidence model depends on publishable
run traces; leaking one secret destroys that guarantee.

### VII. Test-First and Replayable

Core and component logic (event parsing, reducers, view models, adapters)
MUST be developed test-first: tests written and failing before implementation.
Because of Principle I, this logic MUST be testable headlessly by feeding
recorded event streams; every bug fix SHOULD add a replayable event fixture
reproducing it. Widget/visual behavior SHOULD be covered with the underlying
toolkit's snapshot or pilot testing facilities where practical.

**Rationale**: A streaming UI is hard to debug live; replayable fixtures make
correctness cheap to verify and regressions cheap to catch.

### VIII. Example-Driven

Every shipped library feature MUST be demonstrated in at least one runnable
example in the examples gallery. Examples are first-class deliverables: they
MUST run from a fresh checkout with documented steps, stay current with the
public API (a breaking API change is not complete until the examples are
updated), and collectively cover more than one application domain so the
library never drifts toward a single use case.

**Rationale**: Examples are simultaneously documentation, integration tests,
and proof of generality. If a feature cannot be shown working in an example,
it is not done.

## Technology & Platform Constraints

- Language: Python (modern, actively supported versions).
- The library MUST run on common modern terminals on Windows, macOS, Linux,
  and WSL. Features that cannot work on all supported platforms MUST degrade
  gracefully rather than crash.
- Whether the core builds on an existing terminal engine (e.g., Textual,
  prompt_toolkit, Rich) or custom rendering is a deliberate architecture
  decision to be made in the first feature plan's research phase — not
  implicitly through the first dependency added. Re-implementing terminal
  compatibility from scratch requires explicit justification.
- TUIs built with the library MUST remain responsive while long-running work
  streams events; event ingestion and rendering MUST NOT block the UI loop.
- The common event schema MUST be versioned (a `version` field in the event
  envelope) from the first release; schema changes follow the same semantic
  versioning discipline as this constitution.
- New runtime dependencies require justification in the plan's Constitution
  Check; prefer the chosen engine's built-ins over additional packages.

## Development Workflow & Quality Gates

- All feature work follows the Spec Kit flow: specify → clarify → plan →
  tasks → implement, on a feature branch.
- The plan's Constitution Check gate MUST pass before Phase 0 research and be
  re-checked after Phase 1 design; violations MUST be justified in Complexity
  Tracking or the design simplified.
- Tests MUST pass before a feature is considered complete; reducers, adapters,
  and view models MUST NOT merge without headless tests (Principle VII).
- A feature is not complete until demonstrated in a runnable example
  (Principle VIII).
- Code review (human or agent) MUST verify compliance with this constitution,
  especially layer boundaries (Principle II) and public-safety (Principle VI).
- Start simple (YAGNI): the first milestone targets a read-mostly console
  example replaying one run; process control, file editing, and plugin
  systems come later and need their own specs.

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

**Version**: 2.0.0 | **Ratified**: 2026-06-12 | **Last Amended**: 2026-06-12
