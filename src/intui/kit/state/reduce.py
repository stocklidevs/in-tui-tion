"""The ready-made reduction from the standard event vocabulary (FR-002).

Mapping table: specs/002-task-visualization-kit/data-model.md. Pure,
deterministic, upsert-based — out-of-order and unknown events degrade
gracefully (FR-004). Unknown event types leave the state unchanged
(foundation reducer contract).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace
from typing import Any

from intui.events.envelope import Event
from intui.kit.state.model import (
    UNASSIGNED_KEY,
    LaneView,
    TaskBoardState,
    TaskView,
    WorkItemView,
)

_TASK_EVENTS = {"task_created", "task_started", "task_completed", "task_blocked"}
_ITEM_EVENTS = {"work_item_started", "work_item_completed"}
_LANE_EVENTS = {"subagent_started", "subagent_activity", "subagent_completed"}

#: Canonical event types the taskboard reducer consumes (part of the stream
#: contract; the reducer dispatches on these exact sets).
TASKBOARD_EVENT_TYPES = frozenset(_TASK_EVENTS | _ITEM_EVENTS | _LANE_EVENTS)


def taskboard_slice() -> tuple[Any, TaskBoardState]:
    """``(reducer, initial)`` pair for ``compose_reducers(taskboard=...)``."""
    return _reduce, TaskBoardState()


def _key(event: Event, entity_id: str) -> str:
    return f"{event.run_id}:{entity_id}"


def _title(event: Event, fallback: str) -> str:
    name = event.payload.get("name")
    if isinstance(name, str) and name:
        return name
    if event.summary:
        return event.summary
    return fallback


def _completion_status(event: Event) -> str:
    return "failed" if event.status == "failed" else "completed"


def _reduce(state: TaskBoardState, event: Event) -> TaskBoardState:
    if event.type in _TASK_EVENTS:
        return _reduce_task(state, event)
    if event.type in _ITEM_EVENTS:
        return _reduce_item(state, event)
    if event.type in _LANE_EVENTS:
        return _reduce_lane(state, event)
    return state


def _reduce_task(state: TaskBoardState, event: Event) -> TaskBoardState:
    task_id = event.scope.task_id
    if not task_id:
        return state
    key = _key(event, task_id)
    status = {
        "task_created": "pending",
        "task_started": "active",
        "task_blocked": "blocked",
        "task_completed": _completion_status(event),
    }[event.type]
    existing = state.tasks.get(key)
    task = TaskView(
        key=key,
        task_id=task_id,
        title=_title(event, fallback=task_id) if existing is None else existing.title,
        status=status,
        item_counts=existing.item_counts if existing is not None else {},
        last_summary=event.summary or (existing.last_summary if existing else None),
        order=existing.order if existing is not None else len(state.tasks),
    )
    return replace(state, tasks={**state.tasks, key: task})


def _reduce_item(state: TaskBoardState, event: Event) -> TaskBoardState:
    item_id = event.scope.work_item_id
    if not item_id:
        return state
    key = _key(event, item_id)
    parent_id = event.scope.task_id or UNASSIGNED_KEY
    parent_key = _key(event, event.scope.task_id) if event.scope.task_id else UNASSIGNED_KEY
    status = "active" if event.type == "work_item_started" else _completion_status(event)
    existing = state.work_items.get(key)
    item = WorkItemView(
        key=key,
        work_item_id=item_id,
        parent_key=existing.parent_key if existing is not None else parent_key,
        title=_title(event, fallback=item_id) if existing is None else existing.title,
        status=status,
        last_summary=event.summary or (existing.last_summary if existing else None),
        parent_id=existing.parent_id if existing is not None else parent_id,
    )
    work_items: Mapping[str, WorkItemView] = {**state.work_items, key: item}
    tasks = _with_item_counts(state.tasks, work_items, item.parent_key)
    return replace(state, work_items=work_items, tasks=tasks)


def _with_item_counts(
    tasks: Mapping[str, TaskView],
    work_items: Mapping[str, WorkItemView],
    parent_key: str,
) -> Mapping[str, TaskView]:
    parent = tasks.get(parent_key)
    if parent is None:
        return tasks  # unassigned bucket or unseen task: counts derive in selectors
    counts: dict[str, int] = {}
    for item in work_items.values():
        if item.parent_key == parent_key:
            counts[item.status] = counts.get(item.status, 0) + 1
    return {**tasks, parent_key: replace(parent, item_counts=counts)}


def _reduce_lane(state: TaskBoardState, event: Event) -> TaskBoardState:
    lane_id = event.scope.lane_id
    if not lane_id:
        return state
    key = _key(event, lane_id)
    existing = state.lanes.get(key)
    name = _title(event, fallback=lane_id) if existing is None else existing.name
    parent_key = (
        existing.parent_key
        if existing is not None
        else (_key(event, event.scope.task_id) if event.scope.task_id else None)
    )
    if event.type == "subagent_completed":
        status = "completed" if event.status is None or event.status == "passed" else event.status
        terminal = True
        activity = existing.activity if existing is not None else ""
    elif event.type == "subagent_activity":
        status = existing.status if existing is not None else "active"
        terminal = existing.terminal if existing is not None else False
        activity = event.summary or (existing.activity if existing is not None else "")
    else:  # subagent_started
        status = "active"
        terminal = False
        activity = existing.activity if existing is not None else ""
    lane = LaneView(
        key=key,
        name=name,
        status=status,
        parent_key=parent_key,
        activity=activity,
        terminal=terminal,
        last_summary=event.summary or (existing.last_summary if existing else None),
    )
    return replace(state, lanes={**state.lanes, key: lane})
