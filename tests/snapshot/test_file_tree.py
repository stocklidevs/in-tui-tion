"""FileTree widget: renders the nested workspace tree (Pilot)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from textual.app import App, ComposeResult

from intui.app import IntuiApp
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


async def _select(app: Any, pilot: Any, path: str) -> None:
    from textual.widgets import Tree

    tree = app.query_one(FileTree).query_one(Tree)
    tree.focus()
    await pilot.pause()
    node = next(n for n in _walk(tree.root) if n.data == path)
    tree.move_cursor(node)
    await pilot.pause()


def _walk(node: Any) -> Any:
    for child in node.children:
        yield child
        yield from _walk(child)


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


# --- file actions (posted as intents) ----------------------------------------


class _IntentHarness(IntuiApp):
    """An IntuiApp recording delivered intents (for the action tests)."""

    def __init__(self, store: Store) -> None:
        self._delivered: list[Any] = []
        super().__init__(store=store, on_intent=self._record)

    async def _record(self, intent: Any) -> None:
        self._delivered.append(intent)

    def compose(self) -> ComposeResult:
        yield FileTree(file_tree_view())


async def test_open_and_copy_post_intents_for_selected_file() -> None:
    app = _IntentHarness(_store())
    async with app.run_test(size=(80, 24)) as pilot:
        await _select(app, pilot, "src/app.py")
        await pilot.press("o")
        await pilot.press("c")
        await pilot.pause(0.05)
        names = {(i.name, i.payload["path"]) for i in app._delivered}
        assert ("open_file", "src/app.py") in names
        assert ("copy_path", "src/app.py") in names


async def test_directory_selection_posts_nothing() -> None:
    app = _IntentHarness(_store())
    async with app.run_test(size=(80, 24)) as pilot:
        await _select(app, pilot, "src/app.py")  # focus the tree
        from textual.widgets import Tree

        tree = app.query_one(FileTree).query_one(Tree)
        src_dir = next(n for n in _walk(tree.root) if n.data == "src")
        tree.move_cursor(src_dir)
        await pilot.pause()
        assert app.query_one(FileTree).selected_file() is None
        await pilot.press("o")
        await pilot.pause(0.05)
        assert app._delivered == []


async def test_delete_is_confirmed_then_delivered() -> None:
    app = _IntentHarness(_store())
    async with app.run_test(size=(80, 24)) as pilot:
        await _select(app, pilot, "README.md")
        await pilot.press("x")
        await pilot.pause(0.05)
        assert app._delivered == []  # held by the confirmation prompt
        await pilot.press("y")  # confirm
        await pilot.pause(0.05)
        assert [(i.name, i.payload["path"]) for i in app._delivered] == [
            ("delete_file", "README.md")
        ]


async def test_delete_cancel_delivers_nothing() -> None:
    app = _IntentHarness(_store())
    async with app.run_test(size=(80, 24)) as pilot:
        await _select(app, pilot, "README.md")
        await pilot.press("x")
        await pilot.pause(0.05)
        await pilot.press("n")  # cancel
        await pilot.pause(0.05)
        assert app._delivered == []
