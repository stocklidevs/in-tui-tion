"""Workspace slice + file_tree selector + scan_workspace (engine-free)."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from intui.events import Event, Scope
from intui.kit.state import (
    KNOWN_EVENT_TYPES,
    WORKSPACE_EVENT_TYPES,
    file_tree_view,
    scan_workspace,
    workspace_slice,
)
from intui.state import Store, compose_reducers

_seq = 0


def _event(type_: str, **payload: object) -> Event:
    global _seq
    _seq += 1
    return Event(
        version="1",
        event_id=f"e{_seq}",
        run_id="r1",
        timestamp=datetime(2026, 6, 14, tzinfo=UTC),
        type=type_,
        scope=Scope(),
        payload=payload,
    )


def _store() -> Store:
    return Store(compose_reducers(workspace=workspace_slice()))


def _names(nodes: tuple) -> list[str]:
    return [n.name for n in nodes]


def test_files_nest_into_directories() -> None:
    store = _store()
    store.ingest(_event("file_written", path="src/app.py", change_type="added"))
    store.ingest(_event("file_written", path="src/util.py"))
    store.ingest(_event("file_written", path="README.md"))
    roots = file_tree_view()(store.snapshot).roots
    # dirs before files, alpha: src (dir) then README.md (file)
    assert _names(roots) == ["src", "README.md"]
    src = roots[0]
    assert src.is_dir and _names(src.children) == ["app.py", "util.py"]
    assert all(not c.is_dir for c in src.children)


def test_status_added_then_modified() -> None:
    store = _store()
    store.ingest(_event("file_written", path="a.py", change_type="added"))
    roots = file_tree_view()(store.snapshot).roots
    assert roots[0].status == "added"
    store.ingest(_event("file_written", path="a.py"))  # default modified
    roots = file_tree_view()(store.snapshot).roots
    assert roots[0].status == "modified"


def test_repeat_write_no_duplicate() -> None:
    store = _store()
    store.ingest(_event("file_written", path="src/a.py"))
    store.ingest(_event("file_written", path="src/a.py"))
    src = file_tree_view()(store.snapshot).roots[0]
    assert _names(src.children) == ["a.py"]


def test_remove_prunes_file_and_empty_dir() -> None:
    store = _store()
    store.ingest(_event("file_written", path="src/a.py"))
    store.ingest(_event("file_written", path="README.md"))
    store.ingest(_event("file_removed", path="src/a.py"))
    roots = file_tree_view()(store.snapshot).roots
    assert _names(roots) == ["README.md"]  # src dir pruned (now empty)


def test_unknown_remove_ignored() -> None:
    store = _store()
    store.ingest(_event("file_written", path="a.py"))
    store.ingest(_event("file_removed", path="ghost.py"))  # no crash
    assert _names(file_tree_view()(store.snapshot).roots) == ["a.py"]


def test_separators_normalized() -> None:
    store = _store()
    store.ingest(_event("file_written", path="src\\app.py"))
    store.ingest(_event("file_written", path="./src/util.py"))
    src = file_tree_view()(store.snapshot).roots[0]
    assert src.name == "src" and _names(src.children) == ["app.py", "util.py"]


def test_public_safe_redacts_absolute_path() -> None:
    store = _store()
    store.ingest(_event("file_written", path="/home/alice/secret.py"))
    roots = file_tree_view()(store.snapshot).roots  # public_safe default True
    assert all("alice" not in n.name for n in roots)
    # relative path passes through unredacted
    store.ingest(_event("file_written", path="src/app.py"))
    names = {n.name for n in file_tree_view()(store.snapshot).roots}
    assert "src" in names


def test_public_safe_off_shows_raw() -> None:
    store = _store()
    store.ingest(_event("file_written", path="/home/alice/x.py"))
    roots = file_tree_view(public_safe=False)(store.snapshot).roots
    # the absolute path is kept (nested under its segments)
    assert any("home" in n.name or "alice" in str(n.path) for n in _flatten(roots))


def _flatten(nodes: tuple) -> list:
    out = []
    for n in nodes:
        out.append(n)
        out.extend(_flatten(n.children))
    return out


def test_absolute_posix_path_kept_for_actions() -> None:
    # A leading "/" must survive normalization so file actions target the real
    # (absolute) file — regression for a cross-platform bug where strip("/")
    # turned "/tmp/x" into a relative "tmp/x" on POSIX.
    store = _store()
    store.ingest(_event("file_written", path="/var/log/out.log"))
    roots = file_tree_view(public_safe=False)(store.snapshot).roots
    leaf = next(n for n in _flatten(roots) if not n.is_dir)
    assert leaf.path == "/var/log/out.log"


def test_empty_workspace() -> None:
    assert file_tree_view()(_store().snapshot).roots == ()


def test_event_types_in_vocabulary() -> None:
    assert WORKSPACE_EVENT_TYPES <= KNOWN_EVENT_TYPES


def test_file_action_intents() -> None:
    from intui.kit.state import (
        copy_path_intent,
        delete_file_intent,
        open_file_intent,
    )

    op = open_file_intent("src/app.py")
    assert op.name == "open_file" and op.payload["path"] == "src/app.py" and not op.risky
    cp = copy_path_intent("src/app.py")
    assert cp.name == "copy_path" and cp.payload["path"] == "src/app.py"
    dl = delete_file_intent("src/app.py")
    assert dl.name == "delete_file" and dl.payload["path"] == "src/app.py" and dl.risky


def test_file_action_intents_are_not_events() -> None:
    # intents are requests, not stream events
    assert {"open_file", "copy_path", "delete_file"}.isdisjoint(KNOWN_EVENT_TYPES)


def test_scan_workspace_yields_relative_paths(tmp_path: Path) -> None:
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.py").write_text("x", encoding="utf-8")
    (tmp_path / "README.md").write_text("y", encoding="utf-8")
    events = list(scan_workspace(tmp_path))
    paths = sorted(e.payload["path"] for e in events)
    assert paths == ["README.md", "src/app.py"]
    assert all(e.type == "file_written" for e in events)


def test_scan_workspace_feeds_tree(tmp_path: Path) -> None:
    (tmp_path / "pkg").mkdir()
    (tmp_path / "pkg" / "mod.py").write_text("x", encoding="utf-8")
    store = _store()
    for ev in scan_workspace(tmp_path):
        store.ingest(ev)
    roots = file_tree_view()(store.snapshot).roots
    assert roots[0].name == "pkg" and roots[0].children[0].name == "mod.py"
