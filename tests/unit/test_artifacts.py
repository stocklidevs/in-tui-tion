"""Artifact models, reduction, and diff/evidence selectors (headless)."""

from datetime import UTC, datetime

from intui.events import Event, Scope
from intui.kit.state import (
    ArtifactStore,
    DiffArtifact,
    EvidenceArtifact,
    FileDiff,
    artifacts_slice,
    diff_view,
    evidence_view,
)
from intui.state import Store, compose_reducers

UNIFIED = (
    "--- a/src/app.py\n+++ b/src/app.py\n@@ -1 +1 @@\n-old\n+new\n"
    "--- a/secret.txt\n+++ b/C:\\Users\\me\\secret.txt\n@@ -1 +1 @@\n-a\n+b\n"
)


def make_store() -> Store:
    return Store(compose_reducers(artifacts=artifacts_slice()))


def diff_event() -> Event:
    return Event(
        version="1",
        event_id="d1",
        run_id="r1",
        timestamp=datetime(2026, 6, 13, tzinfo=UTC),
        type="diff_ready",
        scope=Scope(),
        payload={"title": "Changes", "unified": UNIFIED},
    )


def evidence_event(eid: str = "e1", **over: object) -> Event:
    payload = {
        "title": "Run evidence",
        "metrics": [
            {"key": "pass_rate", "label": "Pass rate", "value": "92%", "status": "passed"},
            {"key": "failures", "label": "Failure categories", "value": ["timeout", "drift"]},
            {"key": "workdir", "label": "Workdir", "value": "C:\\Users\\me\\run", "unsafe": True},
        ],
    }
    payload.update(over)
    return Event(
        version="1",
        event_id=eid,
        run_id="r1",
        timestamp=datetime(2026, 6, 13, tzinfo=UTC),
        type="evidence_ready",
        scope=Scope(),
        payload=payload,
    )


# --- models ------------------------------------------------------------------


def test_models_value_equality() -> None:
    a = FileDiff(path="x", raw_path="x", added=1, removed=0)
    b = FileDiff(path="x", raw_path="x", added=1, removed=0)
    assert a == b
    assert ArtifactStore() == ArtifactStore()


# --- reduction ---------------------------------------------------------------


def test_diff_ready_reduced_into_store() -> None:
    store = make_store()
    store.ingest(diff_event())
    art: ArtifactStore = store.snapshot.slice("artifacts")
    assert isinstance(art.diff, DiffArtifact)
    assert len(art.diff.files) == 2


def file_diff_event(eid: str, path: str, *, new: str = "x", reset: bool = False) -> Event:
    unified = f"--- a/{path}\n+++ b/{path}\n@@ -1 +1 @@\n-old\n+{new}\n"
    payload: dict[str, object] = {"title": path, "unified": unified}
    if reset:
        payload["reset"] = True
    return Event(
        version="1",
        event_id=eid,
        run_id="r1",
        timestamp=datetime(2026, 6, 13, tzinfo=UTC),
        type="diff_ready",
        scope=Scope(),
        payload=payload,
    )


def test_diff_ready_accumulates_files_by_path() -> None:
    store = make_store()
    store.ingest(file_diff_event("d1", "src/a.py"))
    store.ingest(file_diff_event("d2", "src/b.py"))
    store.ingest(file_diff_event("d3", "src/c.py"))
    files = diff_view()(store.snapshot).files
    assert [f.path for f in files] == ["src/a.py", "src/b.py", "src/c.py"]


def test_diff_ready_same_path_replaces_in_place() -> None:
    store = make_store()
    store.ingest(file_diff_event("d1", "src/a.py", new="first"))
    store.ingest(file_diff_event("d2", "src/b.py"))
    store.ingest(file_diff_event("d3", "src/a.py", new="second"))
    view = diff_view()(store.snapshot)
    assert [f.path for f in view.files] == ["src/a.py", "src/b.py"]  # no duplicate
    body_text = "".join(line.text for line in view.body("src/a.py"))
    assert "second" in body_text and "first" not in body_text


def test_diff_ready_reset_clears_accumulation() -> None:
    store = make_store()
    store.ingest(file_diff_event("d1", "src/a.py"))
    store.ingest(file_diff_event("d2", "src/b.py"))
    store.ingest(file_diff_event("d3", "src/c.py", reset=True))
    files = diff_view()(store.snapshot).files
    assert [f.path for f in files] == ["src/c.py"]


def test_diff_ready_multifile_single_event_still_lists_all() -> None:
    store = make_store()
    store.ingest(diff_event())  # one event, multi-file UNIFIED blob (2 files)
    assert len(diff_view()(store.snapshot).files) == 2


def test_accumulated_diffs_stay_public_safe_by_default() -> None:
    store = make_store()
    store.ingest(file_diff_event("d1", "src/a.py"))
    store.ingest(diff_event())  # carries an unsafe path in the second file
    view = diff_view()(store.snapshot)
    assert all("C:\\Users\\me" not in f.path for f in view.files)


def test_evidence_ready_reduced_into_store() -> None:
    store = make_store()
    store.ingest(evidence_event())
    art: ArtifactStore = store.snapshot.slice("artifacts")
    assert isinstance(art.evidence, EvidenceArtifact)
    assert art.evidence.metrics[0].key == "pass_rate"


def test_latest_of_type_wins() -> None:
    store = make_store()
    store.ingest(evidence_event())
    store.ingest(
        evidence_event(eid="e2", title="Newer", metrics=[{"key": "k", "label": "K", "value": 1}])
    )
    art: ArtifactStore = store.snapshot.slice("artifacts")
    assert art.evidence is not None and art.evidence.title == "Newer"


def test_unknown_event_passes_through() -> None:
    store = make_store()
    before = store.snapshot.slice("artifacts")
    store.ingest(
        Event(
            version="1",
            event_id="x",
            run_id="r",
            timestamp=datetime(2026, 6, 13, tzinfo=UTC),
            type="unrelated",
            scope=Scope(),
        )
    )
    assert store.snapshot.slice("artifacts") == before


# --- diff_view ---------------------------------------------------------------


def test_diff_view_lists_files_with_counts() -> None:
    store = make_store()
    store.ingest(diff_event())
    view = diff_view()(store.snapshot)
    assert len(view.files) == 2
    assert view.files[0].added == 1 and view.files[0].removed == 1


def test_diff_view_public_safe_redacts_paths_by_default() -> None:
    store = make_store()
    store.ingest(diff_event())
    view = diff_view()(store.snapshot)  # default public_safe=True
    assert all("C:\\Users\\me" not in f.path for f in view.files)


def test_diff_view_unsafe_mode_shows_full_paths() -> None:
    store = make_store()
    store.ingest(diff_event())
    view = diff_view(public_safe=False)(store.snapshot)
    assert any("secret.txt" in f.path for f in view.files)


def test_diff_view_body_for_path() -> None:
    store = make_store()
    store.ingest(diff_event())
    view = diff_view()(store.snapshot)
    body = view.body(view.files[0].path)
    assert any(line.text == "new" for line in body)


# --- evidence_view -----------------------------------------------------------


def test_evidence_view_rows_with_labels() -> None:
    store = make_store()
    store.ingest(evidence_event())
    view = evidence_view()(store.snapshot)
    labels = {r.label for r in view.rows}
    assert "Pass rate" in labels and "Failure categories" in labels


def test_evidence_view_list_value_enumerated() -> None:
    store = make_store()
    store.ingest(evidence_event())
    view = evidence_view()(store.snapshot)
    failures = next(r for r in view.rows if r.key == "failures")
    assert "timeout" in failures.value and "drift" in failures.value


def test_evidence_view_redacts_unsafe_value_by_default() -> None:
    store = make_store()
    store.ingest(evidence_event())
    view = evidence_view()(store.snapshot)
    workdir = next(r for r in view.rows if r.key == "workdir")
    assert "C:\\Users\\me\\run" not in workdir.value
    assert workdir.label == "Workdir"  # label preserved


def test_evidence_view_unsafe_mode_shows_value() -> None:
    store = make_store()
    store.ingest(evidence_event())
    view = evidence_view(public_safe=False)(store.snapshot)
    workdir = next(r for r in view.rows if r.key == "workdir")
    assert "run" in workdir.value


def test_views_memoized_per_snapshot() -> None:
    store = make_store()
    store.ingest(diff_event())
    view = diff_view()
    assert view(store.snapshot) is view(store.snapshot)


def test_empty_views() -> None:
    store = make_store()
    assert diff_view()(store.snapshot).files == ()
    assert evidence_view()(store.snapshot).rows == ()
