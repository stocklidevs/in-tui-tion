# Phase 0 Research: Core Library Foundation

**Feature**: `001-core-library-foundation` | **Date**: 2026-06-12

All NEEDS CLARIFICATION items from the Technical Context are resolved here.

## R1. Rendering engine: build on Textual

**Decision**: Build the core library on **Textual** (Textualize), current 6.x
line, as the terminal engine. in-TUI-tion's core wraps Textual behind its own
public API (pipeline, store, view models, intents, signals); applications and
examples program against in-TUI-tion, not Textual directly, except where we
deliberately re-export widget/composition primitives.

**Rationale**:

- Cross-platform terminal compatibility (Windows Terminal, macOS, Linux, WSL)
  is mature — re-implementing this is years of work the constitution requires
  us to justify, and no justification holds for this feature's goals.
- Async-first application loop fits the non-blocking ingestion requirement
  (FR-012): event sources run as async tasks while rendering continues.
- Reactive attributes and message passing map naturally onto our
  store → view-model → widget binding (FR-009).
- CSS-like theming with design tokens supports switchable themes (FR-017).
- First-class testing story: `Pilot` drives apps headlessly and
  `pytest-textual-snapshot` captures visual regressions — directly serving
  Principle VII and SC-005.
- Mouse support, focus handling, and keybindings give keyboard-first plus
  mouse-friendly (Principle IV) without custom input plumbing.
- Actively maintained and stable (6.5.x as of 2025-2026), Python >=3.9.

**Alternatives considered**:

- **prompt_toolkit**: solid input/rendering core, but widgets, layout, and
  theming are lower-level — we would rebuild much of what Textual provides.
- **Rich (Live) alone**: rendering only; no application loop, focus, or input
  model. Insufficient for interactive apps (US3).
- **urwid**: mature but dated API, weaker Windows story, no comparable
  testing/theming facilities.
- **Custom rendering layer**: rejected; the constitution requires explicit
  justification to re-implement terminal compatibility and none exists here.

**Risk and mitigation**: depending on Textual couples us to its release
cadence. Mitigation: the event/state/view-model pipeline (the heart of the
library) is pure Python with zero Textual imports; only the widget/app layer
touches Textual. This keeps the engine swappable in principle and the core
testable without any terminal.

## R2. Language and version: Python 3.11+

**Decision**: Support Python **3.11 through 3.13** initially.

**Rationale**: 3.10 reaches end-of-life in October 2026 — adopting it now buys
months. 3.11+ gives `Self`, exception groups, fine-grained error locations,
and meaningful interpreter speedups that matter for reduce-heavy code.
Textual supports this range.

**Alternatives considered**: 3.9/3.10 floor (broader reach, EOL-bound and
weaker typing); 3.12+ floor (excludes current LTS distros for no needed
feature).

## R3. Packaging and tooling

**Decision**: `src/` layout, **hatchling** build backend, **uv** for
environment/dependency management, **pytest** (+ `pytest-asyncio`,
`pytest-textual-snapshot`) for tests, **ruff** for lint/format, **mypy**
(strict on the pure-Python core) for typing. Import package name: **`intui`**
(`import intui`), distribution name decided at publish time.

**Rationale**: src layout prevents accidental imports of the working tree and
is the standard for libraries. uv + hatchling is the current low-friction
default for new Python libraries. Strict typing on the core is cheap now and
enforces the "pure pipeline, no Textual imports" boundary. `intui` is short,
readable, and unambiguous in code; the repo keeps the in-TUI-tion brand.

**Alternatives considered**: poetry (heavier, slower resolution), setuptools
(more boilerplate), package name `intuition` (collides with an existing PyPI
distribution and reads as a generic word in code).

## R4. Event envelope and recording format

**Decision**: Events are immutable (frozen) dataclasses with the envelope
fields from the spec (`version`, `event_id`, `run_id`, `timestamp`, `type`,
`scope`, `status`, `summary`, `payload`). Recordings are **JSON Lines**
(`.jsonl`): one envelope per line, UTF-8. Envelope schema version starts at
`"1"` and is validated on ingestion; unknown envelope versions are rejected
with a clear error, unknown *event types* flow through untouched (FR's
unknown-type tolerance).

**Rationale**: JSONL is streamable (works for both recordings and future live
pipes), diffable in git, trivially appendable, and human-inspectable —
matching the requirements doc's existing NDJSON progress format from the
seed application. Frozen dataclasses enforce append-only semantics in code.

**Alternatives considered**: SQLite recordings (not diffable, overkill now),
protobuf/msgpack (compact but opaque; can be added later behind the same
source interface), pydantic models (runtime dep the core doesn't need —
hand-rolled validation of one envelope is small; revisit if schemas multiply).

## R5. State store and reduction

**Decision**: Pure-function reducers fold events into an **immutable state
snapshot**; the store keeps the current snapshot plus a monotonically
increasing state version, deduplicates by `event_id`, and isolates reducer
exceptions (failed event reported via stream-health state, prior snapshot
retained). The store is synchronous and engine-agnostic; a thin adapter
bridges store changes into Textual's reactive/message system.

**Rationale**: Determinism (FR-003, SC-002) falls out of pure reducers over
ordered events. Immutability makes snapshot comparison in replay tests
trivial. Keeping the store free of Textual imports preserves headless
testability (FR-005) and the engine-swap option from R1.

**Alternatives considered**: mutable state with change notifications (faster
but kills cheap snapshot equality and replay determinism guarantees);
full event-sourcing frameworks (unneeded dependency weight).

## R6. View models and widget binding

**Decision**: View models are pure projection functions over the snapshot,
memoized per state version. Widgets subscribe by selector; on each store
update the bridge recomputes subscribed view models and updates only widgets
whose view model actually changed (equality check), coalescing bursts so
rendering never lags ingestion (FR-012, SC-003).

**Rationale**: Selector-style derivation is a proven pattern (Redux/reselect)
that satisfies "widgets consume presentation-shaped data" (FR-004/FR-010)
and makes the no-disturbance acceptance scenario (US1-2) testable via
equality of view models.

**Alternatives considered**: widgets reading the snapshot directly (violates
FR-010), per-field observables (finer-grained but more machinery than the
foundation needs).

## R7. Intents, confirmation, and input

**Decision**: User interactions produce **Intent** objects (name + payload +
`risky` flag) delivered to an application-provided async handler (the
adapter seam). The library ships a confirmation flow: intents flagged risky
are held until the user confirms via a modal/inline prompt. All built-in
interactions get keybindings first; mouse bindings supplement.

**Rationale**: Directly implements Principle III and FR-014/015/016. An async
handler keeps the UI loop unblocked while the application reacts (typically
by appending events).

**Alternatives considered**: callback-per-widget wiring (scatters the action
surface, harder to audit), command-bus singletons (global state, hostile to
testing).

## R8. Theming and signal primitives

**Decision**: Themes are named token sets (palette, emphasis, status colors)
mapped onto Textual CSS variables; switching themes swaps tokens at runtime
without widget changes (FR-017). Ship one default dark theme. The foundation
includes one **Signal** primitive: a status-driven indicator widget whose
color, motion (including a swoosh animation mode), and textual/symbolic
counterpart derive from a bound state field via a status→style mapping
(FR-018, Principle V). Reduced-color terminals fall back via Textual's color
degradation plus the mandatory non-color counterpart.

**Rationale**: Tokens-over-CSS-variables is Textual's intended theming path —
minimal invention. One genuinely data-driven signal primitive proves
Principle V in the foundation without pulling the whole component kit
forward.

**Alternatives considered**: bespoke style engine (reinvention), deferring
signals entirely (would leave Principle V untested by the first example).

## R9. Example application

**Decision**: One example, `examples/hello_replay/`: a small full-screen app
that replays a bundled `.jsonl` recording of a simulated multi-step run —
showing a status header with the Signal primitive, a scrolling list of items
derived from events, theme switching, and two intents (one normal, one
risky/confirmable). Runs cross-platform from a fresh checkout via documented
`uv` steps (FR-019/020, SC-001).

**Rationale**: Exercises every foundation capability in one place (Principle
VIII) while staying domain-neutral — it is *not* the agentic console, which
arrives as a later feature.

**Alternatives considered**: starting with the operator console as the first
example (too large; drags component-kit scope into the foundation).
