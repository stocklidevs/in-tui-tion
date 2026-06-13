# Public API Contract: Central View Router

**Feature**: `007-central-view-router` | **Date**: 2026-06-13

Extends 001–006. Layer rule: `intui.kit.state` (new `views` module) imports no
terminal engine; the `ViewRouter` widget in `intui.kit` may.

## `intui.kit.state` (engine-free additions)

```python
@dataclass(frozen=True) class ViewState:
    views: tuple[str, ...]; current: str
@dataclass(frozen=True) class ViewEntry:
    id: str; label: str; selected: bool
@dataclass(frozen=True) class ViewRouterView:
    entries: tuple[ViewEntry, ...]

def view_slice(views: Sequence[str], initial: str | None = None
              ) -> tuple[SliceReducer, ViewState]
def view_router_view(slice_name: str = "views",
                     labels: Mapping[str, str] | None = None) -> Selector[ViewRouterView]
def select_view_intent(view: str) -> Intent      # Intent("select_view", {"view": view})
```

## `intui.kit` (Textual layer)

```python
class ViewRouter(BoundContainer):
    """Central pane that shows the registered view for the current selection.

    Wraps a ContentSwitcher; registers panes by id; falls back to a placeholder
    when the selection is empty or has no registered pane. Binds to
    view_router_view.
    """
    def __init__(self, selector: Selector[ViewRouterView],
                 views: Mapping[str, Widget],
                 *, placeholder: str = "select a view", **kwargs): ...
```

## Compatibility promises

- View selection flows intent → `view_selected` event → state (Principle III);
  `select_view_intent` is the stable way to build the intent.
- The `view_selected` mapping (data-model.md) is part of the contract; adding
  mappings is MINOR, changing existing ones MAJOR.
- The router and the mode model (005) are independent slices; the
  mode→default-view association is an application concern, not library API.
- A selected id with no registered pane renders the placeholder (never crashes).
```
