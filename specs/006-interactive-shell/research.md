# Phase 0 Research: Interactive Shell & Activity Strip

**Feature**: `006-interactive-shell` | **Date**: 2026-06-13

Platform and kit patterns are settled (001–005). The unknowns are small.

## R1. PromptInput wraps the engine Input; submits as an intent

**Decision**: `PromptInput(Widget)` wraps Textual's `Input`. On
`Input.Submitted` it validates non-empty, posts a `prompt_submitted` intent via
`IntuiApp.post_intent`, and clears the field. It is *not* a BoundContainer (no
view-model binding — it is pure input). A helper
`prompt_message_event(text, run_id="")` builds the `message_added` (role=user)
event so apps append the submission in one line (FR-005).

**Rationale**: Reuses the engine's input widget (keyboard handling, cursor,
focus) rather than reinventing it; routing via `post_intent` keeps Principle III
(the prompt never mutates state itself, FR-004). The event helper lives in
engine-free `kit.state.conversation` so it is headlessly testable.

**Alternatives considered**: a custom text-entry widget (reinvents the engine
Input for no benefit); appending the user message inside the prompt (violates
FR-004 — the app owns state mutation).

## R2. ActivityStrip is a full-width Signal preset

**Decision**: `ActivityStrip(Signal)` subclasses the existing Signal with a
built-in R6 status→style map (`ACTIVITY_STYLES`: thinking→swoosh red,
waiting→pulse amber, verifying→swoosh cyan, passed→steady green, history→pulse
violet, failure→strobe red, idle→steady muted) and a wide track sized to the
available width (recomputed on resize). It binds to an app-supplied
activity-state selector.

**Rationale**: The swoosh, color resolution, motion modes, and non-color glyph/
label counterpart already exist in Signal (001) and the theme already has the
R6 status colors. The only new things are the R6 mapping preset and
width-responsive sizing — minimal, high-impact.

**Alternatives considered**: a brand-new widget (throws away the tested Signal
mechanics); keeping it one-line/small (fails R6's "prominent ambient" intent).

## R3. ACTIVITY_STYLES + state vocabulary in engine-free kit state

**Decision**: The R6 activity status names and the `ACTIVITY_STYLES` mapping
live in `intui/kit/state/activity.py` (engine-free; the `StatusStyle`/
`MotionMode` types are already engine-free in `intui.theming`). The strip widget
imports the map. Keeps the mapping unit-testable (every state → distinct
glyph+label, SC-003) without a terminal.

**Rationale**: Same split as the rest of the kit; the table is data and belongs
with the model, the widget is the renderer.

## R4. Width-responsive track sizing

**Decision**: `ActivityStrip` recomputes its track length from `self.size.width`
(minus the label width) on mount and `on_resize`, clamped to a sane minimum so
the label is never clipped (FR-008, SC-005). Signal already renders a track of a
given width; the strip just drives that width from layout.

**Rationale**: Reuses Signal's renderer; only the width input is dynamic.

## R5. Example wiring

**Decision**: In `operator_console`, the `ActivityStrip` docks at the very top
(above the mode strip), bound to the existing `run_status` selector (extended to
emit R6-flavored states). The `PromptInput` docks at the bottom (above the
command bar). The app's `handle_intent` gains a `prompt_submitted` branch:
append the user message, set a transient `thinking` activity state, and schedule
a scripted agent reply (append an agent `message_added`) after a short delay,
then restore the run state.

**Rationale**: Demonstrates the full loop (input → intent → user message → agent
reply → transcript) and the strip lighting up during the response, all through
the real pipeline — the scripted reply is the only simulated part (spec
assumption).
