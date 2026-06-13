# Data Model: Interactive Shell & Activity Strip

**Feature**: `006-interactive-shell` | **Date**: 2026-06-13

Mostly composition; the only new model data is the activity-state mapping and a
small event helper. Both engine-free.

## Activity states (R6)

Vocabulary: `thinking | waiting | verifying | passed | history | failure | idle`.

### ACTIVITY_STYLES

A `Mapping[str, StatusStyle]` (StatusStyle/MotionMode are engine-free, from
`intui.theming`):

| State | Color token | Motion | Glyph | Label |
|-------|-------------|--------|-------|-------|
| thinking | thinking | swoosh | » | thinking |
| waiting | waiting | pulse | ? | waiting |
| verifying | verifying | swoosh | ≈ | verifying |
| passed | success | steady | ✔ | passed |
| history | history | pulse | ◆ | history |
| failure | failure | strobe | ✘ | failed |
| idle | muted | steady | · | idle |

Glyph + label are the mandatory non-color counterparts (SC-003). Unknown
states fall back to a neutral steady style with the raw name as label (FR-009).

`activity_style(state: str) -> StatusStyle` resolves a state (with fallback).

## prompt_submitted intent

`Intent("prompt_submitted", {"text": <typed text>})` — emitted by the prompt on
submit. Not risky.

## prompt_message_event helper

`prompt_message_event(text: str, run_id: str = "", event_id: str | None = None)
-> Event` builds a `message_added` event with `role="user"` and the text, so an
app appends a submission to the conversation in one call. Engine-free (lives
with the conversation model). Event id defaults to a generated unique value.

## Components (presentation contracts)

- **PromptInput**: a single-line input with a prompt glyph (e.g. `❯`). On
  Enter with non-empty text → post `Intent("prompt_submitted", {"text": text})`
  and clear; empty/whitespace → no-op. Keyboard-focusable.
- **ActivityStrip**: a full-width Signal preset bound to an activity-state
  selector; renders `‹track› glyph label` where the track length follows the
  widget width (min track keeps the label visible). Uses `ACTIVITY_STYLES`.

## Presentation rules

- Prompt: `❯ ` prefix; placeholder when empty (e.g. "type a goal…"); clears on
  submit.
- Activity strip: full-width sweeping track in the state color + glyph + label;
  label always present (non-color). Narrow width → shorter track, label kept.
- The strip's failure state uses the fast strobe motion; thinking/verifying
  swoosh; waiting/history pulse; passed/idle steady.
