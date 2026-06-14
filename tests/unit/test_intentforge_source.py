"""IntentForgeSource: adapt an IF ndjson stream (file/iterable + subprocess)."""

from __future__ import annotations

import asyncio
import json
import sys

from intui.adapters import IntentForgeSource
from intui.events.stream import StreamState
from intui.kit.state import artifacts_slice, taskboard_slice
from intui.state import Store, compose_reducers

_DIFF = "--- a/app.py\n+++ b/app.py\n@@ -1 +1 @@\n-a\n+b\n"


def _line(name: str, payload: dict, sequence: int) -> str:
    return json.dumps(
        {
            "type": "run_trace_event",
            "event": {"sequence": sequence, "name": name, "payload": payload},
        }
    )


LINES = [
    _line("matrix_suite_started", {"suite_id": "s1"}, 1),
    _line("case_started", {"case_id": "c1"}, 2),
    _line("assembly_item_started", {"case_id": "w1"}, 3),
    _line("file_diff", {"case_id": "w1", "work_item_id": "w1", "diff": _DIFF}, 4),
    _line("case_finished", {"case_id": "c1", "status": "passed"}, 5),
    json.dumps({"type": "summary", "summary": {"case_pass_rate": 1.0, "quality_issue_count": 0}}),
]


def _store() -> Store:
    return Store(compose_reducers(taskboard=taskboard_slice(), artifacts=artifacts_slice()))


def test_file_iterable_reduces_tasks_diff_and_evidence() -> None:
    store = _store()
    asyncio.run(store.run(IntentForgeSource(LINES)))
    board = store.snapshot.slice("taskboard")
    assert {t.task_id for t in board.tasks.values()} == {"c1"}
    art = store.snapshot.slice("artifacts")
    assert art.diff is not None and len(art.diff.files) >= 1
    assert art.evidence is not None and len(art.evidence.metrics) >= 1


def test_accepts_path(tmp_path) -> None:
    p = tmp_path / "run.ndjson"
    p.write_text("\n".join(LINES) + "\n", encoding="utf-8")
    store = _store()
    asyncio.run(store.run(IntentForgeSource(p)))
    assert store.snapshot.slice("artifacts").evidence is not None


def test_malformed_line_surfaced_not_raised() -> None:
    store = _store()
    health = asyncio.run(store.run(IntentForgeSource(["{not json", LINES[1]])))
    assert health.state == StreamState.ENDED
    assert store.snapshot.health.rejected_count >= 1
    assert store.snapshot.slice("taskboard").tasks  # the good line still reduced


PRODUCER = r"""
import json
print(json.dumps({"type":"run_trace_event","event":{"sequence":1,"name":"case_started","payload":{"case_id":"c1"}}}))
print(json.dumps({"type":"summary","summary":{"case_pass_rate":1.0}}))
"""


def test_from_command_live() -> None:
    store = _store()
    source = IntentForgeSource.from_command([sys.executable, "-c", PRODUCER])
    health = asyncio.run(store.run(source))
    assert health.state == StreamState.ENDED
    assert store.snapshot.slice("taskboard").tasks
    assert store.snapshot.slice("artifacts").evidence is not None
