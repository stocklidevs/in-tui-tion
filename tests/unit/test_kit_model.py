"""Kit view models: immutability, value equality, status presentation table."""

import dataclasses

import pytest

from intui.kit.state import (
    CORE_STATUSES,
    STATUS_PRESENTATION,
    LaneView,
    TaskBoardState,
    TaskView,
    WorkItemView,
    status_presentation,
)


def make_task(**overrides: object) -> TaskView:
    defaults: dict = {
        "key": "run-1:t1",
        "task_id": "t1",
        "title": "Parse the blueprint",
        "status": "active",
        "item_counts": {"active": 1},
        "last_summary": "working",
        "order": 0,
    }
    defaults.update(overrides)
    return TaskView(**defaults)


def test_task_view_is_frozen() -> None:
    task = make_task()
    with pytest.raises(dataclasses.FrozenInstanceError):
        task.status = "completed"  # type: ignore[misc]


def test_task_view_value_equality() -> None:
    assert make_task() == make_task()
    assert make_task() != make_task(status="completed")


def test_work_item_view_value_equality() -> None:
    a = WorkItemView(key="r:w1", work_item_id="w1", parent_key="r:t1", title="x", status="active")
    b = WorkItemView(key="r:w1", work_item_id="w1", parent_key="r:t1", title="x", status="active")
    assert a == b


def test_lane_view_defaults_and_equality() -> None:
    lane = LaneView(key="r:l1", name="verifier", status="active")
    assert lane.terminal is False
    assert lane.parent_key is None
    assert lane == LaneView(key="r:l1", name="verifier", status="active")


def test_taskboard_state_value_equality() -> None:
    t = make_task()
    a = TaskBoardState(tasks={t.key: t}, work_items={}, lanes={})
    b = TaskBoardState(tasks={t.key: t}, work_items={}, lanes={})
    assert a == b
    assert a != TaskBoardState(tasks={}, work_items={}, lanes={})


def test_core_statuses_complete() -> None:
    assert CORE_STATUSES == ("pending", "active", "blocked", "completed", "failed")


def test_presentation_table_covers_every_core_status() -> None:
    for status in CORE_STATUSES:
        style = STATUS_PRESENTATION[status]
        assert style.glyph and style.label  # mandatory non-color counterparts


def test_presentation_glyphs_and_labels_unique() -> None:
    identities = {(s.glyph, s.label) for s in STATUS_PRESENTATION.values()}
    assert len(identities) == len(STATUS_PRESENTATION)


def test_unknown_status_gets_fallback_with_status_as_label() -> None:
    style = status_presentation("totally_custom")
    assert style.glyph == "?"
    assert style.label == "totally_custom"  # unknown statuses presented as-is
