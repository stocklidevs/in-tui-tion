# Quickstart: Central View Router

**Feature**: `007-central-view-router` | **Date**: 2026-06-13

## Run the flagship

```sh
uv sync
uv run python -m examples.operator_console
```

The central space is now driven by a view router. Switch a **mode**
(Plan/Build/Inspect/Review) and the center lands on that mode's default view;
invoke a **view command** (Tasks/Lanes/Diff/Evidence — in the bottom menu or
palette, by key or click) to route the center straight to that view without
changing mode.

## Use the router

```python
from intui.kit import ViewRouter
from intui.kit.state import view_slice, view_router_view, select_view_intent
from intui.state import Store, compose_reducers

VIEWS = ("tasks", "lanes", "diff", "evidence")
store = Store(compose_reducers(views=view_slice(VIEWS), ...))

class Console(IntuiApp):
    def compose(self):
        yield ViewRouter(
            view_router_view(),
            views={
                "tasks": TasksView(),
                "lanes": LanesPanel(lanes_view()),
                "diff": DiffViewer(diff_view()),
                "evidence": EvidencePanel(evidence_view()),
            },
        )

    async def handle_intent(self, intent):
        if intent.name == "select_view":
            self.store.ingest(view_selected_event(intent.payload["view"]))
        if intent.name == "switch_mode":
            mode = intent.payload["mode"]
            self.store.ingest(mode_changed_event(mode))
            default = MODE_DEFAULT_VIEW.get(mode)   # app-owned mapping
            if default:
                self.store.ingest(view_selected_event(default))
```

A view command is just a `Command` whose intent is `select_view_intent("diff")`.

## Test headlessly

```sh
uv run pytest tests/unit -k views
uv run pytest tests/snapshot -k "router or console"
```
