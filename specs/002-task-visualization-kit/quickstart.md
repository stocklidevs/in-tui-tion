# Quickstart: Task Visualization Kit

**Feature**: `002-task-visualization-kit` | **Date**: 2026-06-12

## Run the example

```sh
uv sync
uv run python -m examples.mission_control
```

Replays a recorded run with parallel workers: the chip counts tasks in the
top bar (press `enter`/click to expand), the tree shows tasks with
drill-down into work items (arrow keys navigate, `enter` expands), and the
lanes panel shows each worker's live activity with a Signal indicator.

## Use the kit in your own app (SC-002: under 15 lines per component)

```python
from intui.kit import TaskCounterChip, TaskTree, LanesPanel
from intui.kit.state import taskboard_slice, chip_view, tree_view, lanes_view
from intui.state import Store, compose_reducers

store = Store(compose_reducers(taskboard=taskboard_slice()))

class MyApp(IntuiApp):
    def compose(self):
        yield TaskCounterChip(chip_view())
        yield TaskTree(tree_view())
        yield LanesPanel(lanes_view())
```

Emit the standard vocabulary (`task_created`, `task_started`,
`task_completed`, `task_blocked`, `work_item_started`, `work_item_completed`,
`subagent_started`, `subagent_activity`, `subagent_completed`) and the kit
needs zero custom reducers. Custom state? Bind your own selectors producing
`ChipView`/`TreeView`/`LanesView` shapes instead.

## Test against recordings

```sh
uv run pytest tests/unit -k kit       # headless model/reduction/selectors
uv run pytest tests/snapshot -k "chip or tree or lanes"
```
