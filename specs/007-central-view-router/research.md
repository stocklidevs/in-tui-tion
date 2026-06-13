# Phase 0 Research: Central View Router

**Feature**: `007-central-view-router` | **Date**: 2026-06-13

Platform and kit patterns are settled (001–006). The router intentionally
mirrors the mode model (005), so the unknowns are small.

## R1. View model mirrors the mode model (engine-free)

**Decision**: `intui/kit/state/views.py` with `ViewState` (ordered view ids +
current), `view_slice(views, initial)`, `view_router_view` selector, and
`select_view_intent(view_id)` — a near-copy of `modes.py`. Reduced from
`view_selected` events; unknown ids leave the selection unchanged.

**Rationale**: The mode model already proved this shape (reduce a named-set +
current from an event, switch via intent). Reusing it keeps the router
predictable and headlessly testable (FR-012); it is a *different slice*, not a
reuse of the mode slice, because views are finer and independent of workflow
phase.

**Alternatives considered**: generalizing modes and views into one shared
"selection" abstraction (premature DRY — two consumers is the threshold; if a
third appears, extract then). Keeping them separate matches the "complement"
decision.

## R2. ViewRouter wraps the engine ContentSwitcher

**Decision**: `ViewRouter(BoundContainer)` owns a Textual `ContentSwitcher`.
The application registers panes by id (the same ids the view slice knows). The
router binds to `view_router_view`; on change it sets
`ContentSwitcher.current = f"view-{selected}"`, or shows a placeholder pane when
the selected id has no registered pane / nothing is selected (FR-004/005).

**Rationale**: The operator console already uses a ContentSwitcher for mode
panes (005, research R4); promoting that pattern into a reusable component is
the natural step. ContentSwitcher gives pane mounting + show/hide for free;
the router just drives `current` from reduced state.

**Alternatives considered**: manual show/hide of stacked widgets (reinvents
ContentSwitcher); a library-fixed view set (the app must choose its views).

## R3. Views register via a mapping at construction

**Decision**: `ViewRouter(selector, views={"tasks": factory_or_widget, ...},
placeholder=...)`. Each value composes the pane for that id. The router mounts
each pane inside its ContentSwitcher with id `view-{id}` and a `#view-placeholder`
pane. Registered ids should match the view slice's ids; mismatches fall back to
the placeholder.

**Rationale**: Mirrors how the example already builds mode panes; keeps the
library agnostic to which views exist (FR-005). Panes are ordinary kit widgets,
so a "tasks" view can be a small container composing chip + tree.

## R4. select_view as a command; mode defaults in the app

**Decision**: View routing is exposed as ordinary commands (003) whose intent is
`select_view_intent(id)` — so the bottom menu/palette route the center by key or
click with no new machinery (FR-007). The mode→default-view mapping lives in the
application: on a `mode_changed`, the app emits a `view_selected` for that mode's
default (FR-008/009). The library does not couple the two slices.

**Rationale**: Reuses commands wholesale; keeps modes and views decoupled per
the "complement" decision. The app is the only place that knows both its modes
and its views, so the mapping belongs there.

## R5. Example wiring

**Decision**: `operator_console` replaces its mode-pane ContentSwitcher with a
`ViewRouter` registering `tasks` (chip + tree), `lanes`, `diff`, `evidence`.
The bottom command menu gains view commands (Tasks/Lanes/Diff/Evidence →
`select_view`). The app maps modes to defaults (Plan→tasks, Build→tasks,
Inspect→diff, Review→evidence) by emitting `view_selected` in its
`mode_changed`/`switch_mode` handling. Conversation + activity strip + prompt
stay persistent around the router.

**Rationale**: Demonstrates the complement relationship end to end (modes set a
default view; commands route precisely) over the existing recorded run — no new
fixture needed beyond the view/mode events the app emits.
