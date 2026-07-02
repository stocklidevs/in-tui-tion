# Console UX Redesign — Design

**Date:** 2026-07-01
**Status:** Approved (design); ready for implementation planning
**Scope:** `intui.console` rendering layer only — no changes to events, state,
reducers, selectors, or the canonical vocabulary. This is pure presentation.

## Problem

The current `ConsoleApp` (`src/intui/console/app.py`) has three UX problems the
maintainer wants fixed:

1. **The "chat window" is a log, not a conversation.** `ConversationLog` renders
   every entry as a flat `tag: text` line in one `Static`, pinned to a 38-column
   side column (`#conversation-col`). It reads like `journalctl`.
2. **Information is presented as flat text in boxes.** Evidence is `label: value`
   lines; the `ViewRouter` shows exactly one panel at a time; little visual
   hierarchy, no emphasis on what changed.
3. **Effects are underused.** The only motion is the `ActivityStrip` KITT sweep.
   No transitions on view change, no highlight when new data arrives, no motion
   tying "an event happened" to "something changed on screen."

## Direction (approved)

Borrow Grok Build's TUI arrangement, keep in-TUI-tion's visual identity.

### 1. The chat window becomes the run timeline
Delete the side `#conversation-col` / `ConversationLog` as the primary surface.
The **center column *is* a single-column vertical timeline** of the run: events
stream top-to-bottom in arrival order (collected → per-module results → failures
→ what's running now → summary). This is the maintainer's concept #2 — narrative
and milestones, not speaker messages.

### 2. Prompt pinned to the floor, output above
The command/prompt input docks at the **bottom** (Grok-style). A live
slash-command palette hovers just above it (`/rerun-failed`, `/diff`, `/scrub`,
…). History scrolls above. You type where your eyes already are.

### 3. Keep our identity where Grok would flatten it
- **Status vocabulary stays glyph + label**, never color alone (Principle IV):
  `✓ passed`, `✗ failed`, `◷ running`, `◆ thinking`.
- **The KITT swoosh survives and is elevated** to a state indicator, not decor.
- **Structured cards stay** — the evidence summary is a bordered card, not lines.

### 4. Failures are callouts, not log lines
A failure renders as a **bordered callout** (left red border) with the assertion
inline — the "flat text" fix made concrete.

## Motion language (Principle V — meaningful motion)

- **KITT swoosh = run state.** The `Signal` strip under the header tracks the
  active phase, and **its color is the state**: cyan `verifying`, red
  `thinking`/`failure`, amber `waiting`, green pulse on clean finish. Motion +
  color + the adjacent glyph+label all move together. Rendered with the existing
  `Signal` primitive (bright `█` core, `▓▒░` glow shoulders); we widen the glow
  and raise fps so the character-cell sweep reads as gliding, not stepping.
- **One-shot failure flash.** When a failure callout appears, it flashes red
  once (single PULSE) then settles to the quiet bordered state — grabs you, then
  gets out of the way.
- **Streaming rows swoosh in** rather than snapping, so the feed feels alive.
- **Palette / mode selection** gets a quick STROBE/fade.

All motion respects `MotionMode` (reduced-motion falls back to static states).

## Panel behavior (approved: inline diffs + overlays)

The six detail surfaces (diff, files, metrics, evidence, lanes, tasks) behave as
a **blend**:

- **Diffs expand inline.** Selecting a failed/changed item in the timeline
  unfolds its `DiffViewer` right there in the flow — the diff belongs where the
  failure is.
- **Browsable panels open as slash-command overlays.** `/files`, `/metrics`,
  `/lanes`, `/evidence`, `/tasks` open the rich panel full-screen over the
  timeline; Esc closes. The timeline stays the uncluttered home base.

Existing keybindings (t/l/f/d/e/m, palette, scrub) are preserved as accelerators
that map onto the overlay/inline actions.

## What stays exactly as-is
- All of `intui.events`, `intui.state`, `intui.kit.state`, selectors, view-models.
- The canonical event vocabulary and the reducers.
- The kit widgets themselves (`DiffViewer`, `EvidencePanel`, `MetricsPanel`,
  `FileTree`, `LanesPanel`, `TaskTree`, `Signal`, `ActivityStrip`,
  `CommandBar`/`CommandPalette`, `PromptInput`) — reused, re-composed, restyled;
  not rewritten from scratch.

## Constraints / non-negotiables
- Principle II layering: only the rendering layer changes; core stays engine-free.
- Principle IV: non-color glyph+label for every status; keyboard-first; honor
  reduced-motion.
- Principle VI: public-safe rendering unchanged (redaction stays on by default).
- Principle VII: the integration test in `tests/integration/test_console_app.py`
  is updated alongside; new timeline/overlay behavior is covered.

## Open items for the plan
- New widgets vs. re-compose: a `RunTimeline` widget over the conversation/
  taskboard/artifacts slices; an overlay host; a floor-docked prompt region.
- How inline diff expansion binds to a timeline row (selection → expand region).
- Exact `Signal` fps/glow tuning for the "glide" feel and per-state color map.
- Migration of the six single-key bindings onto overlay open/close.
