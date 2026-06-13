"""Selector factories projecting TaskBoardState into component view models."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from intui.kit.state.model import (
    CORE_STATUSES,
    UNASSIGNED_KEY,
    TaskBoardState,
    status_presentation,
)
from intui.state.snapshot import Snapshot
from intui.viewmodels.selector import Selector

# --- Chip --------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ChipRow:
    key: str
    title: str
    status: str
    glyph: str
    label: str


def _empty_counts() -> Mapping[str, int]:
    return {}


@dataclass(frozen=True, slots=True)
class ChipView:
    total: int = 0
    completed: int = 0
    status_counts: Mapping[str, int] = field(default_factory=_empty_counts)
    rows: tuple[ChipRow, ...] = ()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ChipView):
            return NotImplemented
        return (
            self.total == other.total
            and self.completed == other.completed
            and dict(self.status_counts) == dict(other.status_counts)
            and self.rows == other.rows
        )


def _board(snapshot: Snapshot, slice_name: str) -> TaskBoardState:
    return snapshot.slice(slice_name)  # type: ignore[no-any-return]


def taskboard_from(snapshot: Snapshot, slice_name: str = "taskboard") -> TaskBoardState:
    """Convenience accessor for the taskboard slice."""
    return _board(snapshot, slice_name)


def chip_view(slice_name: str = "taskboard") -> Selector[ChipView]:
    def project(snapshot: Snapshot) -> ChipView:
        board = _board(snapshot, slice_name)
        ordered = sorted(board.tasks.values(), key=lambda t: t.order)
        counts: dict[str, int] = {}
        for task in ordered:
            bucket = task.status if task.status in CORE_STATUSES else "other"
            counts[bucket] = counts.get(bucket, 0) + 1
        rows = tuple(
            ChipRow(
                key=task.key,
                title=task.title,
                status=task.status,
                glyph=status_presentation(task.status).glyph,
                label=status_presentation(task.status).label,
            )
            for task in ordered
        )
        return ChipView(
            total=len(ordered),
            completed=counts.get("completed", 0),
            status_counts=counts,
            rows=rows,
        )

    return Selector(project)


# --- Tree --------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ItemRow:
    key: str
    title: str
    status: str
    glyph: str
    label: str


@dataclass(frozen=True, slots=True)
class TaskRow:
    key: str
    title: str
    status: str
    glyph: str
    label: str
    items: tuple[ItemRow, ...] = ()


@dataclass(frozen=True, slots=True)
class TreeView:
    tasks: tuple[TaskRow, ...] = ()


def tree_view(slice_name: str = "taskboard") -> Selector[TreeView]:
    def project(snapshot: Snapshot) -> TreeView:
        board = _board(snapshot, slice_name)
        items_by_parent: dict[str, list[ItemRow]] = {}
        for item in board.work_items.values():
            parent = item.parent_key if item.parent_key in board.tasks else UNASSIGNED_KEY
            style = status_presentation(item.status)
            items_by_parent.setdefault(parent, []).append(
                ItemRow(
                    key=item.key,
                    title=item.title,
                    status=item.status,
                    glyph=style.glyph,
                    label=style.label,
                )
            )
        rows = []
        for task in sorted(board.tasks.values(), key=lambda t: t.order):
            style = status_presentation(task.status)
            rows.append(
                TaskRow(
                    key=task.key,
                    title=task.title,
                    status=task.status,
                    glyph=style.glyph,
                    label=style.label,
                    items=tuple(items_by_parent.pop(task.key, ())),
                )
            )
        orphans = [row for rows_ in items_by_parent.values() for row in rows_]
        if orphans:
            style = status_presentation("pending")
            rows.append(
                TaskRow(
                    key=UNASSIGNED_KEY,
                    title="unassigned",
                    status="pending",
                    glyph=style.glyph,
                    label=style.label,
                    items=tuple(orphans),
                )
            )
        return TreeView(tasks=tuple(rows))

    return Selector(project)


# --- Lanes -------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class LaneRow:
    key: str
    name: str
    status: str
    glyph: str
    label: str
    activity: str
    terminal: bool
    last_summary: str | None


@dataclass(frozen=True, slots=True)
class LanesView:
    lanes: tuple[LaneRow, ...] = ()


def lane_status_view(lane_key: str, slice_name: str = "taskboard") -> Selector[str]:
    """Project a single lane's status (for binding a per-lane Signal)."""

    def project(snapshot: Snapshot) -> str:
        board = _board(snapshot, slice_name)
        lane = board.lanes.get(lane_key)
        return lane.status if lane is not None else "pending"

    return Selector(project)


def lanes_view(
    slice_name: str = "taskboard", *, parent_key: str | None = None
) -> Selector[LanesView]:
    def project(snapshot: Snapshot) -> LanesView:
        board = _board(snapshot, slice_name)
        rows = tuple(
            LaneRow(
                key=lane.key,
                name=lane.name,
                status=lane.status,
                glyph=status_presentation(lane.status).glyph,
                label=status_presentation(lane.status).label,
                activity=lane.activity,
                terminal=lane.terminal,
                last_summary=lane.last_summary,
            )
            for lane in board.lanes.values()
            if parent_key is None or lane.parent_key == parent_key
        )
        return LanesView(lanes=rows)

    return Selector(project)
