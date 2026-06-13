"""The parallel-run fixture reduces deterministically into the expected board."""

from pathlib import Path

from intui.events import read_recording
from intui.kit.state import UNASSIGNED_KEY, TaskBoardState, taskboard_slice
from intui.state import Snapshot, Store, compose_reducers

FIXTURE = Path(__file__).parent / "fixtures" / "parallel_run.jsonl"


def replay() -> Snapshot:
    store = Store(compose_reducers(taskboard=taskboard_slice()))
    for event in read_recording(FIXTURE):
        store.ingest(event)
    return store.snapshot


def test_fixture_replay_is_deterministic() -> None:
    assert replay() == replay()


def test_fixture_final_board_shape() -> None:
    board: TaskBoardState = replay().slice("taskboard")
    statuses = {t.task_id: t.status for t in board.tasks.values()}
    assert statuses == {
        "t-schema": "blocked",
        "t-services": "completed",
        "t-verify": "completed",
        "t-report": "pending",
    }
    items = {i.work_item_id: i for i in board.work_items.values()}
    assert items["w-relations"].status == "failed"
    assert items["w-stray"].parent_key == UNASSIGNED_KEY
    lanes = {lane.name: lane for lane in board.lanes.values()}
    assert lanes["schema-worker"].terminal and lanes["schema-worker"].status == "failed"
    assert lanes["service-worker"].terminal and lanes["service-worker"].status == "completed"
