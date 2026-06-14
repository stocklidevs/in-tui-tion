"""Kit selectors: chip counts, tree shape, lane filtering — headless."""

from datetime import UTC, datetime

from intui.events import Event, Scope
from intui.kit.state import (
    UNASSIGNED_KEY,
    chip_view,
    lanes_view,
    taskboard_slice,
    tree_view,
)
from intui.state import Store, compose_reducers


def make_event(
    event_id: str,
    type_: str,
    *,
    task_id: str | None = None,
    work_item_id: str | None = None,
    lane_id: str | None = None,
    status: str | None = None,
    summary: str | None = None,
    **payload: object,
) -> Event:
    return Event(
        version="1",
        event_id=event_id,
        run_id="run-1",
        timestamp=datetime(2026, 6, 12, tzinfo=UTC),
        type=type_,
        scope=Scope(task_id=task_id, work_item_id=work_item_id, lane_id=lane_id),
        status=status,
        summary=summary,
        payload=payload,
    )


def make_store() -> Store:
    return Store(compose_reducers(taskboard=taskboard_slice()))


# --- chip_view ---------------------------------------------------------------


def test_chip_counts_track_tasks() -> None:
    store = make_store()
    chip = chip_view()
    for i in range(14):
        store.ingest(make_event(f"c{i}", "task_created", task_id=f"t{i}"))
    for i in range(7):
        store.ingest(make_event(f"d{i}", "task_completed", task_id=f"t{i}", status="passed"))
    vm = chip(store.snapshot)
    assert vm.total == 14
    assert vm.completed == 7


def test_chip_empty_state() -> None:
    vm = chip_view()(make_store().snapshot)
    assert vm.total == 0
    assert vm.rows == ()


def test_chip_status_counts_with_other_bucket() -> None:
    store = make_store()
    store.ingest(make_event("e1", "task_started", task_id="t1"))
    store.ingest(make_event("e2", "task_blocked", task_id="t2"))
    store.ingest(make_event("e3", "subagent_completed", lane_id="x"))  # not a task
    store.ingest(make_event("e4", "task_completed", task_id="t3", status="weird"))
    vm = chip_view()(store.snapshot)
    assert vm.status_counts["active"] == 1
    assert vm.status_counts["blocked"] == 1
    assert vm.status_counts["completed"] == 1  # "weird" is not "failed" => completed
    assert vm.total == 3


def test_chip_rows_have_noncolor_identity() -> None:
    store = make_store()
    store.ingest(make_event("e1", "task_started", task_id="t1", summary="Parse"))
    row = chip_view()(store.snapshot).rows[0]
    assert row.glyph and row.label and row.title == "Parse"


def test_chip_memoizes_per_snapshot() -> None:
    store = make_store()
    chip = chip_view()
    store.ingest(make_event("e1", "task_started", task_id="t1"))
    assert chip(store.snapshot) is chip(store.snapshot)


# --- tree_view ---------------------------------------------------------------


def test_tree_nests_work_items_under_tasks() -> None:
    store = make_store()
    store.ingest(make_event("e1", "task_started", task_id="t1", summary="Build"))
    store.ingest(
        make_event("e2", "work_item_started", task_id="t1", work_item_id="w1", summary="compile")
    )
    vm = tree_view()(store.snapshot)
    assert len(vm.tasks) == 1
    task_row = vm.tasks[0]
    assert task_row.title == "Build"
    assert [i.title for i in task_row.items] == ["compile"]


def test_tree_orphans_grouped_under_unassigned() -> None:
    store = make_store()
    store.ingest(make_event("e1", "work_item_started", work_item_id="w9", summary="stray"))
    vm = tree_view()(store.snapshot)
    unassigned = [t for t in vm.tasks if t.key == UNASSIGNED_KEY]
    assert len(unassigned) == 1
    assert [i.title for i in unassigned[0].items] == ["stray"]


def test_tree_preserves_first_seen_order() -> None:
    store = make_store()
    store.ingest(make_event("e1", "task_started", task_id="z"))
    store.ingest(make_event("e2", "task_started", task_id="a"))
    vm = tree_view()(store.snapshot)
    assert [t.title for t in vm.tasks] == ["z", "a"]


def test_tree_rows_carry_status_identity() -> None:
    store = make_store()
    store.ingest(make_event("e1", "task_blocked", task_id="t1"))
    row = tree_view()(store.snapshot).tasks[0]
    assert row.glyph and row.label == "blocked"


def test_tree_synthesizes_parent_for_items_without_task_event() -> None:
    # Work items carry a parent id (task_id) but no task event was emitted.
    store = make_store()
    store.ingest(
        make_event(
            "e1", "work_item_started", task_id="suite-x", work_item_id="w1", summary="scaffold"
        )
    )
    store.ingest(
        make_event(
            "e2",
            "work_item_completed",
            task_id="suite-x",
            work_item_id="w2",
            status="passed",
            summary="api",
        )
    )
    vm = tree_view()(store.snapshot)
    parents = [t for t in vm.tasks if t.title == "suite-x"]
    assert len(parents) == 1
    assert [i.title for i in parents[0].items] == ["scaffold", "api"]
    assert parents[0].key != UNASSIGNED_KEY


def test_tree_synthesized_parent_status_rolls_up() -> None:
    store = make_store()
    store.ingest(
        make_event("e1", "work_item_completed", task_id="s", work_item_id="w1", status="passed")
    )
    store.ingest(make_event("e2", "work_item_started", task_id="s", work_item_id="w2"))  # active
    row = next(t for t in tree_view()(store.snapshot).tasks if t.title == "s")
    assert row.status == "active"  # active outranks completed in the roll-up


def test_tree_real_task_takes_precedence_over_synthesized() -> None:
    store = make_store()
    store.ingest(
        make_event("e1", "work_item_started", task_id="t1", work_item_id="w1", summary="item")
    )
    store.ingest(make_event("e2", "task_started", task_id="t1", summary="Real Task"))
    vm = tree_view()(store.snapshot)
    assert [t.title for t in vm.tasks] == ["Real Task"]  # no separate synthesized node
    assert [i.title for i in vm.tasks[0].items] == ["item"]


def test_tree_parented_and_unparented_coexist() -> None:
    store = make_store()
    store.ingest(
        make_event("e1", "work_item_started", task_id="s", work_item_id="w1", summary="child")
    )
    store.ingest(make_event("e2", "work_item_started", work_item_id="w2", summary="orphan"))
    titles = {t.title for t in tree_view()(store.snapshot).tasks}
    assert "s" in titles and "unassigned" in titles


# --- lanes_view --------------------------------------------------------------


def test_lanes_rows_with_activity_and_terminal() -> None:
    store = make_store()
    store.ingest(make_event("e1", "subagent_started", lane_id="l1", name="verifier"))
    store.ingest(make_event("e2", "subagent_activity", lane_id="l1", summary="checking"))
    vm = lanes_view()(store.snapshot)
    assert len(vm.lanes) == 1
    lane = vm.lanes[0]
    assert lane.name == "verifier"
    assert lane.activity == "checking"
    assert lane.terminal is False

    store.ingest(make_event("e3", "subagent_completed", lane_id="l1", status="passed"))
    lane = lanes_view()(store.snapshot).lanes[0]
    assert lane.terminal is True


def test_lanes_scope_filter() -> None:
    store = make_store()
    store.ingest(make_event("e1", "subagent_started", lane_id="l1", task_id="t1"))
    store.ingest(make_event("e2", "subagent_started", lane_id="l2", task_id="t2"))
    scoped = lanes_view(parent_key="run-1:t1")(store.snapshot)
    assert [lane.key for lane in scoped.lanes] == ["run-1:l1"]


def test_lanes_independent_updates() -> None:
    store = make_store()
    store.ingest(make_event("e1", "subagent_started", lane_id="l1", name="a"))
    store.ingest(make_event("e2", "subagent_started", lane_id="l2", name="b"))
    store.ingest(make_event("e3", "subagent_activity", lane_id="l1", summary="working on a"))
    vm = lanes_view()(store.snapshot)
    by_name = {lane.name: lane for lane in vm.lanes}
    assert by_name["a"].activity == "working on a"
    assert by_name["b"].activity == ""
