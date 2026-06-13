# Implementation Plan: Central View Router

**Branch**: `007-central-view-router` | **Date**: 2026-06-13 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/007-central-view-router/spec.md`

## Summary

A finer central-pane selector that complements the workflow modes: an
engine-free view model (`view_slice`/`view_router_view`/`select_view_intent`,
reduced from `view_selected`, mirroring the mode model), and a `ViewRouter`
component wrapping a `ContentSwitcher` that shows the registered pane for the
current selection (placeholder fallback). View routing is exposed as ordinary
commands; the `operator_console` example drives its central space through the
router with tasks/lanes/diff/evidence views, routes them via view commands, and
preselects a default view per mode (an app-owned mapping). Decisions in
[research.md](research.md); model in [data-model.md](data-model.md).

## Technical Context

**Language/Version**: Python 3.11–3.13 (unchanged)

**Primary Dependencies**: Textual 6.x (present, ContentSwitcher). **No new deps.**

**Storage**: JSONL recordings (unchanged).

**Testing**: pytest headless for `kit.state.views` (reduction + selector +
intent); Pilot for `ViewRouter` (select → pane, placeholder); example test for
command-routing + mode-default preselect.

**Target Platform**: unchanged (Windows/macOS/Linux/WSL terminals).

**Project Type**: library + examples gallery (unchanged).

**Performance Goals**: router re-renders only on selection change (FR-006);
responsive under streaming.

**Constraints**: view model engine-free (lint + guard, FR-012); selection via
intent → event (FR-007, Principle III); router/mode models decoupled (FR-008/009).

**Scale/Scope**: view model + ViewRouter + view commands + example wiring. Files
browser, compare, graph views are out of scope (router can host later).

## Constitution Check

| # | Principle | Status | Notes |
|---|-----------|--------|-------|
| I | Structured State | ✅ PASS | `view_router_view` is a selector over the snapshot; selection reduced from `view_selected`. |
| II | Layered Architecture | ✅ PASS | `views.py` joins engine-free `kit.state`; `ViewRouter` is a layer-2 widget on public APIs. |
| III | Actions Are Intents | ✅ PASS | Selection is a `select_view` intent → `view_selected` event → state; no UI-only mutation. |
| IV | Keyboard-First, Accessible | ✅ PASS | Views routable by command key/palette; placeholder + selection identifiable without color. |
| V | Meaningful Motion | ✅ PASS (n/a) | No new motion. |
| VI | Public-Safe | ✅ PASS | Routed views (diff/evidence) keep 004's default-on redaction. |
| VII | Test-First, Replayable | ✅ PASS | View model headless test-first; router + example via Pilot. |
| VIII | Example-Driven | ✅ PASS | The flagship's central space is driven by the router with view commands + mode defaults (FR-010). |
| — | New deps justified | ✅ PASS | None — reuses ContentSwitcher + commands. |

**Post-Phase-1 re-check (2026-06-13)**: artifacts add no dependencies and hold
the layer boundary. GATE: PASS — Complexity Tracking empty.

## Project Structure

### Documentation (this feature)

```text
specs/007-central-view-router/
├── plan.md  research.md  data-model.md  quickstart.md
├── contracts/router-api.md
├── checklists/requirements.md
└── tasks.md (Phase 2 via /speckit-tasks)
```

### Source Code (repository root)

```text
src/intui/
├── kit/
│   ├── state/
│   │   └── views.py          # ── engine-free ── ViewState, view_slice,
│   │                         #   view_router_view, ViewEntry/ViewRouterView,
│   │                         #   select_view_intent
│   └── view_router.py        # ViewRouter (BoundContainer over ContentSwitcher)

tests/
├── unit/
│   └── test_views.py             # reduction + selector + select_view_intent
└── snapshot/
    ├── test_view_router.py       # select -> pane, unknown -> placeholder, empty
    └── test_operator_console.py  # extend: view command routes center; mode preselects default

examples/operator_console/        # central space -> ViewRouter; view commands; mode->default-view map
```

**Structure Decision**: view model in engine-free `kit.state.views` (mirrors
`modes.py`); `ViewRouter` is a `BoundContainer` wrapping `ContentSwitcher`
(promoting the example's mode-pane pattern into a reusable component); view
selection rides the existing command/intent machinery; the mode→default-view
mapping stays in the example (decoupled models).

## Complexity Tracking

No constitutional violations — table intentionally empty.
