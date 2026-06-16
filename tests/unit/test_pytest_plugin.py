"""The pytest plugin: `pytest --intui` emits a canonical, reducible stream."""

from __future__ import annotations

from pathlib import Path

from intui.events import read_recording
from intui.kit.state import (
    artifacts_slice,
    conversation_slice,
    run_status_slice,
    taskboard_slice,
    tree_view,
)
from intui.state import Store, compose_reducers

pytest_plugins = ["pytester"]

_SUITE = {
    "test_alpha.py": (
        "def test_pass():\n    assert 1 == 1\n\ndef test_fail():\n    assert 1 == 2\n"
    ),
    "test_beta.py": (
        "import pytest\n\n"
        "def test_ok():\n    assert True\n\n"
        "@pytest.mark.skip(reason='nope')\n"
        "def test_skipped():\n    assert False\n"
    ),
}


def _reduce(path: Path) -> Store:
    store = Store(
        compose_reducers(
            taskboard=taskboard_slice(),
            artifacts=artifacts_slice(),
            conversation=conversation_slice(),
            run_status=run_status_slice(),
        )
    )
    for event in read_recording(path):
        store.ingest(event)
    return store


def test_emits_canonical_stream_that_reduces(pytester) -> None:  # type: ignore[no-untyped-def]
    pytester.makepyfile(**_SUITE)
    out = pytester.path / "run.jsonl"
    result = pytester.runpytest_subprocess("--intui", str(out))
    # 2 passed (test_pass, test_ok), 1 failed, 1 skipped
    result.assert_outcomes(passed=2, failed=1, skipped=1)
    assert out.is_file()

    events = read_recording(out)
    types = [e.type for e in events]
    assert types[0] == "run_started"
    assert types[-1] == "run_failed"  # the suite had a failure
    assert events[-1].status == "failed"
    assert "evidence_ready" in types
    assert types.count("work_item_started") == 4
    assert types.count("work_item_completed") == 4

    store = _reduce(out)
    # modules nest as tasks; tests are work items under them
    titles = {t.title for t in tree_view()(store.snapshot).tasks}
    assert any("test_alpha.py" in t for t in titles)
    assert any("test_beta.py" in t for t in titles)
    board = store.snapshot.slice("taskboard")
    statuses = {wi.title: wi.status for wi in board.work_items.values()}
    assert statuses["test_pass"] == "completed"
    assert statuses["test_fail"] == "failed"
    assert statuses["test_skipped"] == "completed"  # skipped -> non-failed -> completed
    # a failure produced a conversation message
    convo = store.snapshot.slice("conversation")
    assert any("FAILED" in e.text and "test_fail" in e.text for e in convo.entries)
    # run status reflects the failure
    assert store.snapshot.slice("run_status") == "failure"
    # evidence summary counts
    ev = store.snapshot.slice("artifacts").evidence
    metrics = {m.key: m.value for m in ev.metrics}
    assert metrics["passed"] == 2 and metrics["failed"] == 1 and metrics["skipped"] == 1


def test_inert_without_flag(pytester) -> None:  # type: ignore[no-untyped-def]
    pytester.makepyfile(test_x="def test_ok():\n    assert True\n")
    result = pytester.runpytest_subprocess()
    result.assert_outcomes(passed=1)
    assert not (pytester.path / "intui-pytest.jsonl").exists()
    assert list(pytester.path.glob("*.jsonl")) == []
