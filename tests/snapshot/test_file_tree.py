"""FileTree widget: renders the nested workspace tree (Pilot)."""

from __future__ import annotations

from datetime import UTC, datetime

from textual.app import App, ComposeResult

from intui.events import Event, Scope
from intui.kit import FileTree
from intui.kit.state import file_tree_view, workspace_slice
from intui.state import Store, compose_reducers
from intui.widgets.bridge import StoreBridge

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


class _Harness(App[None]):
    def __init__(self, store: Store) -> None:
        super().__init__()
        self.store = store
        self.bridge = StoreBridge(store, self)

    def compose(self) -> ComposeResult:
        yield FileTree(file_tree_view())


def _store() -> Store:
    store = Store(compose_reducers(workspace=workspace_slice()))
    store.ingest(_event("file_written", path="src/app.py", change_type="added"))
    store.ingest(_event("file_written", path="src/util.py"))
    store.ingest(_event("file_written", path="README.md"))
    return store


async def test_file_tree_renders_dirs_and_files() -> None:
    app = _Harness(_store())
    async with app.run_test(size=(80, 24)) as pilot:
        await pilot.pause()
        tree = app.query_one(FileTree)
        paths = tree.paths()
        assert "src" in paths and "src/app.py" in paths and "README.md" in paths


async def test_file_tree_keyboard_navigates() -> None:
    app = _Harness(_store())
    async with app.run_test(size=(80, 24)) as pilot:
        await pilot.pause()
        tree = app.query_one(FileTree)
        tree.query_one("Tree").focus()
        await pilot.pause()
        await pilot.press("down")
        await pilot.pause()
        assert app.is_running  # navigation does not crash


async def test_file_tree_refreshes_on_new_event() -> None:
    store = _store()
    app = _Harness(store)
    async with app.run_test(size=(80, 24)) as pilot:
        await pilot.pause()
        store.ingest(_event("file_written", path="docs/guide.md"))
        await pilot.pause()
        assert "docs/guide.md" in app.query_one(FileTree).paths()
