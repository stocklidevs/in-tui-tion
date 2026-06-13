"""The ready-made taskboard reduction: every mapping-table row + tolerance rules."""

from datetime import UTC, datetime

from intui.events import Event, Scope
from intui.kit.state import UNASSIGNED_KEY, TaskBoardState, taskboard_slice
from intui.state import Store, compose_reducers


def make_event(
    event_id: str,
    type_: str,
    *,
    run_id: str = "run-1",
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
        run_id=run_id,
        timestamp=datetime(2026, 6, 12, tzinfo=UTC),
        type=type_,
        scope=Scope(task_id=task_id, work_item_id=work_item_id, lane_id=lane_id),
        status=status,
        summary=summary,
        payload=payload,
    )


def make_store() -> Store:
    return Store(compose_reducers(taskboard=taskboard_slice()))


def board(store: Store) -> TaskBoardState:
    return store.snapshot.slice("taskboard")


def test_task_created_is_pending() -> None:
    store = make_store()
    store.ingest(make_event("e1", "task_created", task_id="t1", summary="Parse"))
    task = board(store).tasks["run-1:t1"]
    assert task.status == "pending"
    assert task.title == "Parse"


def test_task_started_is_active() -> None:
    store = make_store()
    store.ingest(make_event("e1", "task_started", task_id="t1"))
    assert board(store).tasks["run-1:t1"].status == "active"


def test_task_completed_passed_and_failed() -> None:
    store = make_store()
    store.ingest(make_event("e1", "task_completed", task_id="t1", status="passed"))
    store.ingest(make_event("e2", "task_completed", task_id="t2", status="failed"))
    assert board(store).tasks["run-1:t1"].status == "completed"
    assert board(store).tasks["run-1:t2"].status == "failed"


def test_task_blocked() -> None:
    store = make_store()
    store.ingest(make_event("e1", "task_blocked", task_id="t1"))
    assert board(store).tasks["run-1:t1"].status == "blocked"


def test_work_item_lifecycle_and_parent() -> None:
    store = make_store()
    store.ingest(make_event("e1", "task_started", task_id="t1"))
    store.ingest(make_event("e2", "work_item_started", task_id="t1", work_item_id="w1"))
    item = board(store).work_items["run-1:w1"]
    assert item.status == "active"
    assert item.parent_key == "run-1:t1"
    store.ingest(
        make_event("e3", "work_item_completed", task_id="t1", work_item_id="w1", status="failed")
    )
    assert board(store).work_items["run-1:w1"].status == "failed"


def test_orphan_work_item_goes_to_unassigned() -> None:
    store = make_store()
    store.ingest(make_event("e1", "work_item_started", work_item_id="w9"))
    assert board(store).work_items["run-1:w9"].parent_key == UNASSIGNED_KEY


def test_lane_lifecycle() -> None:
    store = make_store()
    store.ingest(make_event("e1", "subagent_started", lane_id="l1", name="verifier"))
    lane = board(store).lanes["run-1:l1"]
    assert lane.name == "verifier"
    assert lane.status == "active"
    assert lane.terminal is False

    store.ingest(make_event("e2", "subagent_activity", lane_id="l1", summary="checking API"))
    lane = board(store).lanes["run-1:l1"]
    assert lane.activity == "checking API"

    store.ingest(make_event("e3", "subagent_completed", lane_id="l1", status="passed"))
    lane = board(store).lanes["run-1:l1"]
    assert lane.terminal is True
    assert lane.status == "completed"


def test_lane_scoped_to_parent_task() -> None:
    store = make_store()
    store.ingest(make_event("e1", "subagent_started", lane_id="l1", task_id="t1"))
    assert board(store).lanes["run-1:l1"].parent_key == "run-1:t1"


def test_out_of_order_completion_creates_task() -> None:
    store = make_store()
    store.ingest(make_event("e1", "task_completed", task_id="ghost", status="passed"))
    assert board(store).tasks["run-1:ghost"].status == "completed"


def test_duplicate_task_ids_across_runs_stay_distinct() -> None:
    store = make_store()
    store.ingest(make_event("e1", "task_started", task_id="t1", run_id="run-a"))
    store.ingest(make_event("e2", "task_completed", task_id="t1", run_id="run-b", status="passed"))
    tasks = board(store).tasks
    assert tasks["run-a:t1"].status == "active"
    assert tasks["run-b:t1"].status == "completed"


def test_unknown_event_types_pass_through() -> None:
    store = make_store()
    before = board(store)
    store.ingest(make_event("e1", "totally_unrelated"))
    assert board(store) == before


def test_unknown_status_preserved_verbatim() -> None:
    store = make_store()
    store.ingest(make_event("e1", "subagent_completed", lane_id="l1", status="weird_state"))
    assert board(store).lanes["run-1:l1"].status == "weird_state"


def test_task_order_is_first_seen() -> None:
    store = make_store()
    store.ingest(make_event("e1", "task_started", task_id="b"))
    store.ingest(make_event("e2", "task_started", task_id="a"))
    tasks = list(board(store).tasks.values())
    assert [t.task_id for t in tasks] == ["b", "a"]
    assert tasks[0].order < tasks[1].order


def test_reduction_is_deterministic() -> None:
    events = [
        make_event("e1", "task_created", task_id="t1", summary="Parse"),
        make_event("e2", "task_started", task_id="t1"),
        make_event("e3", "work_item_started", task_id="t1", work_item_id="w1"),
        make_event("e4", "subagent_started", lane_id="l1", name="verifier"),
        make_event("e5", "task_completed", task_id="t1", status="passed"),
    ]
    a, b = make_store(), make_store()
    for e in events:
        a.ingest(e)
    for e in events:
        b.ingest(e)
    assert board(a) == board(b)
