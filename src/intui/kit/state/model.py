"""Kit view models and the shared status vocabulary (data-model.md)."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from intui.theming.signal_style import MotionMode, StatusStyle

CORE_STATUSES: tuple[str, ...] = ("pending", "active", "blocked", "completed", "failed")

UNASSIGNED_KEY = "unassigned"
"""Bucket key for work items whose parent task is unknown."""

STATUS_PRESENTATION: Mapping[str, StatusStyle] = {
    "pending": StatusStyle(color="muted", motion=MotionMode.STEADY, glyph="·", label="pending"),
    "active": StatusStyle(color="thinking", motion=MotionMode.SWOOSH, glyph="»", label="active"),
    "blocked": StatusStyle(color="waiting", motion=MotionMode.PULSE, glyph="▲", label="blocked"),
    "completed": StatusStyle(color="success", motion=MotionMode.STEADY, glyph="✔", label="done"),
    "failed": StatusStyle(color="failure", motion=MotionMode.STROBE, glyph="✘", label="failed"),
}
"""Shared glyph/label/motion table. Glyph + label are the mandatory
non-color counterparts (Principle IV)."""


def status_presentation(status: str) -> StatusStyle:
    """Resolve any status to a presentation; unknown statuses keep their
    name as the label with a neutral glyph (never blank, never crash)."""
    style = STATUS_PRESENTATION.get(status)
    if style is not None:
        return style
    return StatusStyle(color="muted", motion=MotionMode.STEADY, glyph="?", label=status)


def _empty_counts() -> Mapping[str, int]:
    return {}


@dataclass(frozen=True, slots=True)
class TaskView:
    key: str
    task_id: str
    title: str
    status: str
    item_counts: Mapping[str, int] = field(default_factory=_empty_counts)
    last_summary: str | None = None
    order: int = 0

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, TaskView):
            return NotImplemented
        return (
            self.key == other.key
            and self.task_id == other.task_id
            and self.title == other.title
            and self.status == other.status
            and dict(self.item_counts) == dict(other.item_counts)
            and self.last_summary == other.last_summary
            and self.order == other.order
        )


@dataclass(frozen=True, slots=True)
class WorkItemView:
    key: str
    work_item_id: str
    parent_key: str
    title: str
    status: str
    last_summary: str | None = None
    #: Raw parent id (the work item's ``scope.task_id``), or ``UNASSIGNED_KEY``
    #: when it has no parent. Titles a synthesized parent node in the tree when
    #: no explicit task event exists for the parent.
    parent_id: str = UNASSIGNED_KEY


@dataclass(frozen=True, slots=True)
class LaneView:
    key: str
    name: str
    status: str
    parent_key: str | None = None
    activity: str = ""
    terminal: bool = False
    last_summary: str | None = None


def _empty_tasks() -> Mapping[str, TaskView]:
    return {}


def _empty_items() -> Mapping[str, WorkItemView]:
    return {}


def _empty_lanes() -> Mapping[str, LaneView]:
    return {}


@dataclass(frozen=True, slots=True)
class TaskBoardState:
    """The derived slice all kit components consume."""

    tasks: Mapping[str, TaskView] = field(default_factory=_empty_tasks)
    work_items: Mapping[str, WorkItemView] = field(default_factory=_empty_items)
    lanes: Mapping[str, LaneView] = field(default_factory=_empty_lanes)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, TaskBoardState):
            return NotImplemented
        return (
            dict(self.tasks) == dict(other.tasks)
            and dict(self.work_items) == dict(other.work_items)
            and dict(self.lanes) == dict(other.lanes)
        )
