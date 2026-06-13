# Public API Contract: Task Visualization Kit

**Feature**: `002-task-visualization-kit` | **Date**: 2026-06-12

Extends the 001 contract. Layer rule: `intui.kit.state` imports no terminal
engine; `intui.kit` component modules may.

## `intui.kit.state` (engine-free)

```python
@dataclass(frozen=True) class TaskView: ...      # fields per data-model.md
@dataclass(frozen=True) class WorkItemView: ...
@dataclass(frozen=True) class LaneView: ...
@dataclass(frozen=True) class TaskBoardState:
    tasks: Mapping[str, TaskView]
    work_items: Mapping[str, WorkItemView]
    lanes: Mapping[str, LaneView]

UNASSIGNED_KEY: str                              # orphan work-item bucket

def taskboard_slice() -> tuple[SliceReducer, TaskBoardState]
    # Ready-made reduction of the standard vocabulary; mount via
    # compose_reducers(taskboard=taskboard_slice()).

def taskboard_from(snapshot: Snapshot, slice_name: str = "taskboard") -> TaskBoardState

# Selector factories (bindable to any slice name / custom state per FR-003):
def chip_view(slice_name: str = "taskboard") -> Selector[ChipView]
def tree_view(slice_name: str = "taskboard") -> Selector[TreeView]
def lanes_view(slice_name: str = "taskboard", *, parent_key: str | None = None) -> Selector[LanesView]

@dataclass(frozen=True) class ChipView:
    total: int; completed: int
    status_counts: Mapping[str, int]             # includes "other" bucket
    rows: tuple[ChipRow, ...]                    # glyph/label/title per task

@dataclass(frozen=True) class TreeView:  ...     # tasks with nested item rows
@dataclass(frozen=True) class LanesView: ...     # lane rows (Signal status + texts)

STATUS_PRESENTATION: Mapping[str, StatusStyle]   # shared glyph/label/token table
```

## `intui.kit` (Textual layer)

```python
class TaskCounterChip(BoundContainer):
    def __init__(self, selector: Selector[ChipView] = chip_view(), ...): ...
    # Keyboard + mouse expand/collapse; compact/narrow/empty forms.

class TaskTree(BoundContainer):
    def __init__(self, selector: Selector[TreeView] = tree_view(), ...): ...
    # Wraps the engine Tree: navigation, visible focus, per-task expansion
    # preserved across refreshes.

class LanesPanel(BoundContainer):
    def __init__(self, selector: Selector[LanesView] = lanes_view(), ...): ...
    # One row per lane: Signal-driven indicator, name, activity, last event.
```

## `intui.widgets` (foundation addition)

```python
class BoundContainer(Widget):
    """Selector-bound container: same value-equality refresh contract as
    BoundWidget; subclasses implement sync_view(vm) to reconcile children."""
```

## Compatibility promises

- The standard event mapping table (data-model.md) is part of this contract;
  adding mappings is MINOR, changing existing ones is MAJOR.
- Components depend only on the view shapes above — custom state stores
  satisfying them are first-class (FR-003).
