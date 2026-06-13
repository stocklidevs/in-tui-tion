"""The inspect fixture reduces deterministically into diff + evidence."""

from pathlib import Path

from intui.events import read_recording
from intui.kit.state import ArtifactStore, artifacts_slice, diff_view, evidence_view
from intui.state import Snapshot, Store, compose_reducers

FIXTURE = Path(__file__).parent / "fixtures" / "inspect_run.jsonl"


def replay() -> Snapshot:
    store = Store(compose_reducers(artifacts=artifacts_slice()))
    for event in read_recording(FIXTURE):
        store.ingest(event)
    return store.snapshot


def test_replay_is_deterministic() -> None:
    assert replay() == replay()


def test_fixture_has_diff_and_evidence() -> None:
    art: ArtifactStore = replay().slice("artifacts")
    assert art.diff is not None and len(art.diff.files) == 3
    assert art.evidence is not None and len(art.evidence.metrics) == 7


def test_public_safe_view_redacts_fixture_secrets() -> None:
    snap = replay()
    diff = diff_view()(snap)  # public-safe default
    assert all("C:\\Users\\operator" not in row.path for row in diff.files)
    evidence = evidence_view()(snap)
    workdir = next(r for r in evidence.rows if r.key == "workdir")
    assert "run-42" not in workdir.value


def test_binary_file_flagged() -> None:
    art: ArtifactStore = replay().slice("artifacts")
    assert art.diff is not None
    binary = next(f for f in art.diff.files if f.path.endswith("logo.png"))
    assert binary.no_text_diff is True
