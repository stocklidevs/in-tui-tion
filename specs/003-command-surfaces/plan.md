# Implementation Plan: Command Surfaces

**Branch**: `003-command-surfaces` | **Date**: 2026-06-12 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/003-command-surfaces/spec.md`

## Summary

The interaction layer (R7): an engine-free `Command`/`CommandRegistry` model
with a state-derived `command_view` selector and a headless fuzzy matcher,
plus two Textual surfaces over the same registry — `CommandBar` (always-visible
bottom menu) and `CommandPalette` (searchable modal). Both invoke through the
foundation's `post_intent`, so risky-action confirmation and the
no-direct-mutation rule are inherited from feature 001. Decisions in
[research.md](research.md); model in [data-model.md](data-model.md).

## Technical Context

**Language/Version**: Python 3.11–3.13 (unchanged)

**Primary Dependencies**: Textual 6.x (present). **No new runtime deps** — the
fuzzy matcher is in-house (research R4).

**Storage**: N/A (registry is in-memory; commands declared in app code).

**Testing**: pytest headless for `kit.state.commands` (registry, availability,
matcher); Pilot for the bar and palette; both risky paths verified headlessly.

**Target Platform**: unchanged (Windows/macOS/Linux/WSL terminals).

**Project Type**: library + examples gallery (unchanged).

**Performance Goals**: surfaces re-render only on input change (FR-016);
palette filters a 20-command registry within a frame (SC-004).

**Constraints**: `kit.state.commands` engine-free (lint + guard); availability
re-checked at fire time (research R5); no color-only state (FR-015).

**Scale/Scope**: command model + 2 surfaces + example wiring. Slash parsing in
a conversation surface, chords, and command arguments are out of scope.

## Constitution Check

| # | Principle | Status | Notes |
|---|-----------|--------|-------|
| I | Structured State | ✅ PASS | `command_view` is a selector over the snapshot; availability derives from state. |
| II | Layered Architecture | ✅ PASS | Command model joins engine-free `kit.state` (guard + ruff ban); surfaces are layer-2 widgets using only public APIs. |
| III | Actions Are Intents | ✅ PASS | Commands emit `Intent` via `post_intent`; no direct state mutation; availability re-checked at fire time. |
| IV | Keyboard-First, Accessible | ✅ PASS | Both surfaces keyboard-operable with visible focus; disabled/selected states marked non-color (FR-015, SC-006). |
| V | Meaningful Motion | ✅ PASS (n/a) | No new motion; nothing decorative added. |
| VI | Public-Safe | ✅ PASS | Renders command labels declared by the app; no evidence surfaces. |
| VII | Test-First, Replayable | ✅ PASS | Registry/availability/matcher headless test-first; surfaces via Pilot. |
| VIII | Example-Driven | ✅ PASS | `mission_control` gains a command bar + palette with a risky command (FR-017). |
| — | New deps justified | ✅ PASS | None — fuzzy matcher in-house (R4). |

**Post-Phase-1 re-check (2026-06-12)**: artifacts add no dependencies and hold
the layer boundary. GATE: PASS — Complexity Tracking empty.

## Project Structure

### Documentation (this feature)

```text
specs/003-command-surfaces/
├── plan.md  research.md  data-model.md  quickstart.md
├── contracts/commands-api.md
├── checklists/requirements.md
└── tasks.md (Phase 2 via /speckit-tasks)
```

### Source Code (repository root)

```text
src/intui/
├── kit/
│   ├── state/
│   │   └── commands.py      # ── engine-free ── Command, CommandRegistry,
│   │                        #   CommandEntry/View, command_view selector,
│   │                        #   match_score / filter_commands
│   ├── command_bar.py       # CommandBar (BoundContainer)
│   └── command_palette.py   # CommandPalette (ModalScreen)
└── app.py                   # + IntuiApp.open_command_palette(registry)

tests/
├── unit/test_commands.py            # registry, availability, matcher (headless)
└── snapshot/
    ├── test_command_bar.py          # menu render, key/click invoke, disabled,
    │                                 #   risky confirm, overflow
    └── test_command_palette.py      # open, filter, select, invoke, dismiss, empty

examples/mission_control/app.py      # add CommandBar + palette opener + a risky command
```

**Structure Decision**: command model in engine-free `kit.state.commands`
(mirrors 002's `state` split); `CommandBar` is a `BoundContainer` (002) and
`CommandPalette` follows the `ConfirmScreen` modal pattern (001). Both invoke
through the existing `post_intent` path — no new action mechanism.

## Complexity Tracking

No constitutional violations — table intentionally empty.
