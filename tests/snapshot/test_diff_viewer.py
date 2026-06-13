"""US1 + US3: the diff viewer — file list, selection, green/red body, public-safe."""

from datetime import UTC, datetime
from typing import Any

from textual.app import ComposeResult

from intui.app import IntuiApp
from intui.events import Event, Scope
from intui.kit import DiffViewer
from intui.kit.state import artifacts_slice, diff_view
from intui.state import Store, compose_reducers

UNIFIED = (
    "--- a/src/app.py\n+++ b/src/app.py\n@@ -1,2 +1,3 @@\n import os\n"
    "-old = 1\n+new = 2\n+extra = 3\n"
    "--- a/cfg.toml\n+++ b/C:\\Users\\op\\secret\\cfg.toml\n@@ -1 +1 @@\n-x = 1\n+x = 2\n"
    "--- a/logo.png\n+++ b/logo.png\nBinary files a/logo.png and b/logo.png differ\n"
)


def diff_event(eid: str = "d1") -> Event:
    return Event(
        version="1",
        event_id=eid,
        run_id="r1",
        timestamp=datetime(2026, 6, 13, tzinfo=UTC),
        type="diff_ready",
        scope=Scope(),
        payload={"title": "Changes", "unified": UNIFIED},
    )


class DiffApp(IntuiApp):
    def __init__(self, *, public_safe: bool = True, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.viewer = DiffViewer(diff_view(public_safe=public_safe))

    def compose(self) -> ComposeResult:
        yield self.viewer


def build(public_safe: bool = True) -> tuple[DiffApp, Store]:
    store = Store(compose_reducers(artifacts=artifacts_slice()))
    return DiffApp(store=store, public_safe=public_safe), store


async def test_lists_changed_files_with_counts() -> None:
    app, store = build()
    async with app.run_test() as pilot:
        await pilot.pause()
        store.ingest(diff_event())
        await pilot.pause(0.05)
        rows = app.viewer.file_rows()
        assert len(rows) == 3
        app_row = next(r for r in rows if "app.py" in r)
        assert "+2" in app_row and "-1" in app_row


async def test_select_file_shows_its_body() -> None:
    app, store = build()
    async with app.run_test() as pilot:
        await pilot.pause()
        store.ingest(diff_event())
        await pilot.pause(0.05)
        app.viewer.select_path("src/app.py")
        await pilot.pause(0.05)
        body = app.viewer.body_text()
        assert "+new = 2" in body
        assert "-old = 1" in body
        assert " import os" in body  # context line carries a space marker


async def test_add_remove_distinguishable_without_color() -> None:
    app, store = build()
    async with app.run_test() as pilot:
        await pilot.pause()
        store.ingest(diff_event())
        await pilot.pause(0.05)
        app.viewer.select_path("src/app.py")
        await pilot.pause(0.05)
        lines = app.viewer.body_text().splitlines()
        assert any(line.startswith("+") for line in lines)
        assert any(line.startswith("-") for line in lines)


async def test_binary_file_placeholder() -> None:
    app, store = build()
    async with app.run_test() as pilot:
        await pilot.pause()
        store.ingest(diff_event())
        await pilot.pause(0.05)
        app.viewer.select_path("logo.png")
        await pilot.pause(0.05)
        assert "no text diff" in app.viewer.body_text().lower()


async def test_empty_state() -> None:
    app, _ = build()
    async with app.run_test() as pilot:
        await pilot.pause()
        assert "no changes" in app.viewer.file_list_text().lower()


async def test_public_safe_redacts_absolute_path() -> None:
    app, store = build(public_safe=True)
    async with app.run_test() as pilot:
        await pilot.pause()
        store.ingest(diff_event())
        await pilot.pause(0.05)
        rows = " ".join(app.viewer.file_rows())
        assert "C:" not in rows or "secret" not in rows  # absolute path redacted


async def test_unsafe_mode_shows_full_path() -> None:
    app, store = build(public_safe=False)
    async with app.run_test() as pilot:
        await pilot.pause()
        store.ingest(diff_event())
        await pilot.pause(0.05)
        rows = " ".join(app.viewer.file_rows())
        assert "secret" in rows


async def test_selection_preserved_across_update() -> None:
    app, store = build()
    async with app.run_test() as pilot:
        await pilot.pause()
        store.ingest(diff_event())
        await pilot.pause(0.05)
        app.viewer.select_path("src/app.py")
        await pilot.pause(0.05)
        store.ingest(diff_event(eid="d2"))  # new diff artifact, same paths
        await pilot.pause(0.05)
        assert app.viewer.selected_path() == "src/app.py"
        assert "+new = 2" in app.viewer.body_text()
