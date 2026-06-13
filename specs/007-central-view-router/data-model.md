# Data Model: Central View Router

**Feature**: `007-central-view-router` | **Date**: 2026-06-13

Engine-free, immutable, mirrors the mode model (005).

## ViewState (slice)

| Field | Type | Notes |
|-------|------|-------|
| `views` | tuple[str, ...] | Ordered registered view ids (seeded at slice creation). |
| `current` | str | Selected view id; defaults to the first seeded view (or ""). |

### Standard event mapping

| Event type | Effect |
|------------|--------|
| `view_selected` | If `payload["view"]` is a known view id, set `current` to it; unknown → unchanged. |
| anything else | unchanged. |

`view_slice(views, initial=None)` → `(reducer, ViewState(views, initial or views[0]))`.

## ViewRouterView

`entries: tuple[ViewEntry, ...]` where `ViewEntry(id, label, selected)`;
memoized selector `view_router_view(slice="views")`. (Label defaults to the id
title-cased; the selector accepts an optional label map.)

## select_view intent

`select_view_intent(view: str) -> Intent` → `Intent("select_view",
{"view": view})`. The app appends a `view_selected` event with that id
(intent → event → state; FR-007). Not risky.

## ViewRouter (presentation contract)

- Constructed with `views: Mapping[str, Widget|factory]` and an optional
  `placeholder`. Mounts each pane as `view-{id}` in a ContentSwitcher plus a
  `view-placeholder` pane.
- Binds to `view_router_view`; on selection change sets the ContentSwitcher's
  current pane to `view-{current}`, or the placeholder when `current` is empty
  or unregistered (FR-004/005).
- Only the central pane changes on selection (FR-004); surrounding surfaces are
  untouched.

## Mode → default view (application-supplied)

A plain mapping the app owns, e.g.:

```text
{"Plan": "tasks", "Build": "tasks", "Inspect": "diff", "Review": "evidence"}
```

On `mode_changed` (or in the `switch_mode` handler), the app emits a
`view_selected` for the mode's default (FR-008). The library does not store or
enforce this mapping — modes and views stay decoupled (FR-009).

## Presentation rules

- View command labels carry the view name textually (non-color); the selected
  view is reflected by which pane is shown (and optionally a selected marker in a
  view bar, if an app adds one).
- Empty/placeholder: when nothing valid is selected, the router shows an explicit
  placeholder pane (e.g. "select a view"), never blank.
