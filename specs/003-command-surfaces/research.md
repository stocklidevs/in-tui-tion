# Phase 0 Research: Command Surfaces

**Feature**: `003-command-surfaces` | **Date**: 2026-06-12

Platform decisions are settled (Textual engine, engine-free pipeline, kit
patterns from 002). This phase resolves only command-surface unknowns.

## R1. Command model lives in the engine-free kit state

**Decision**: The `Command` and `CommandRegistry` are pure dataclasses/logic
in `intui/kit/state/commands.py` (engine-free; joins the layering guard).
Availability is a `Callable[[Snapshot], bool]`. A `command_view(registry)`
selector projects `CommandView` (each command + current enabled flag),
consumed by both surfaces — exactly the selector-over-snapshot pattern from
002.

**Rationale**: Commands reference the foundation `Intent` (already
engine-free) and derive availability from `Snapshot`; nothing here needs the
terminal engine. Keeping it in `kit.state` makes both surfaces data-driven and
headlessly testable (FR-002/003, SC-003/005).

**Alternatives considered**: putting `Command` in foundation `intui.actions`
(it is intent-adjacent, but availability-over-snapshot and registry semantics
are higher-level kit concerns — keep the foundation minimal); a class
hierarchy of command types (a single dataclass with an intent template is
simpler and sufficient).

## R2. Bottom menu: a BoundContainer of command buttons

**Decision**: `CommandBar(BoundContainer)` binds to `command_view(...)`,
rendering a horizontal row of focusable entries (`key  label`), disabled when
unavailable. Invocation calls `app.post_intent(command.intent)` — reusing the
risky-confirmation path from 001 unchanged. Overflow beyond width collapses
into a trailing "… more" entry that opens the palette (FR-008).

**Rationale**: `BoundContainer` already gives value-equality refresh and
bridge registration (002). Routing through `post_intent` means risky
confirmation (FR-013) and the no-direct-mutation rule (FR-006) come for free.

**Alternatives considered**: a `Footer`-derived widget (Textual's Footer is
binding-driven, not state-availability-driven — wrong data source); rendering
plain text (loses click + focus per-item).

## R3. Palette: a custom modal over the shared registry (not Textual's)

**Decision**: `CommandPalette(ModalScreen)` — a custom overlay listing
commands from the same registry, with an input for the query and a result
list. Fuzzy match via a small subsequence scorer in engine-free
`kit.state.commands` (so ranking is unit-testable headlessly, SC-004).
Selecting invokes via the same `post_intent` path and dismisses.

**Rationale**: Textual ships a command palette (Ctrl+P) backed by its
"provider" system, but it is keyed to Textual constructs, not our
state-derived availability + intent registry, and its ranking isn't ours to
unit-test. A thin custom modal over our one registry keeps both surfaces
driven by the same data (FR-004) and keeps the matcher headless-testable.
The confirmation modal pattern (`ConfirmScreen`) from 001 is the template.

**Alternatives considered**: adopting Textual's palette (couples command
availability/labels to its provider API, splits the source of truth);
non-modal inline search (palette overlay matches the R7 mental model and
avoids stealing layout space).

## R4. Fuzzy matching: in-house subsequence scorer

**Decision**: A small pure function `match_score(query, text) -> int | None`
(case-insensitive subsequence with contiguity/word-boundary bonuses);
`None` = no match. Ranking sorts by score then registry order. Lives in
`kit.state.commands`, fully unit-tested.

**Rationale**: Avoids a dependency (constitution: justify new deps), keeps the
matcher deterministic and headlessly tested (SC-004), and the algorithm is
small. Textual's `fuzzy` matcher exists but is internal/engine-side and not
meant for our headless tests.

**Alternatives considered**: `rapidfuzz` (runtime dep for a tiny need —
rejected); exact substring only (fails the "subsequence-friendly" requirement
FR-010).

## R5. Availability re-check at fire time

**Decision**: Both surfaces re-evaluate a command's availability against the
*current* store snapshot at invocation, not the rendered snapshot. If false,
the invocation is dropped (FR-014, SC-005).

**Rationale**: State streams continuously; a command can lapse between render
and key press. Re-checking at fire time closes that race without locking the
UI.

## R6. Key handling and overflow

**Decision**: The `CommandBar` registers command keys as Textual bindings on
the bar widget (scoped to the app via the bar), so menu keys work whenever the
app has focus, and resolve deterministically. Commands without a key are
palette-only (FR: command with no key). Width overflow is computed on resize:
fit N entries, collapse the rest behind "… more".

**Rationale**: Binding on the widget keeps keys discoverable and avoids
silently shadowing unrelated app bindings (edge case); resize-driven overflow
keeps the always-visible guarantee without clipping (FR-008).
