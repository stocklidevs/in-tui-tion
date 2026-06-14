"""ConsoleApp: zero-config console renders a canonical stream, navigates views
by keyboard, honors public-safe, and reflects stream end — no application code."""

from __future__ import annotations

from pathlib import Path

from intui.console import build_console
from intui.events import NdjsonStreamSource, StreamState
from intui.kit import ViewRouter
from intui.kit.state import evidence_view

RECORDING = (
    Path(__file__).parent.parent.parent / "examples" / "operator_console" / "recording.jsonl"
)


def _source(rate: float = 2000.0) -> NdjsonStreamSource:
    # Reuse the flagship recording (it also carries mode_changed events the
    # viewer simply ignores — proving unknown types pass through).
    return NdjsonStreamSource(RECORDING, event_record_types=("run_trace_event",), rate=rate)


async def _drain(app: object, pilot: object) -> None:
    for _ in range(200):
        if app.store.snapshot.health.state is not StreamState.LIVE:  # type: ignore[attr-defined]
            break
        await pilot.pause(0.02)  # type: ignore[attr-defined]
    await pilot.pause()  # type: ignore[attr-defined]


async def test_renders_canonical_stream_into_slices() -> None:
    app = build_console(_source())
    async with app.run_test(size=(120, 40)) as pilot:
        await _drain(app, pilot)
        art = app.store.snapshot.slice("artifacts")
        assert art.diff is not None and len(art.diff.files) == 3
        assert art.evidence is not None
        assert len(app.store.snapshot.slice("conversation").entries) >= 5
        assert app.store.snapshot.slice("taskboard").tasks
        assert app.store.snapshot.health.state is StreamState.ENDED


async def test_views_are_keyboard_navigable() -> None:
    app = build_console(_source())
    async with app.run_test(size=(120, 40)) as pilot:
        await _drain(app, pilot)
        for key, view in [
            ("l", "lanes"),
            ("f", "files"),
            ("d", "diff"),
            ("e", "evidence"),
            ("t", "tasks"),
        ]:
            await pilot.press(key)
            await pilot.pause(0.05)
            assert app.query_one(ViewRouter).current_view() == view
        assert app.is_running


async def test_files_view_shows_workspace_tree() -> None:
    from intui.events import MemorySource
    from intui.kit import FileTree

    lines = [
        {
            "version": "1",
            "event_id": "f1",
            "run_id": "r",
            "timestamp": "2026-06-14T10:00:00Z",
            "type": "file_written",
            "scope": {},
            "payload": {"path": "src/app.py", "change_type": "added"},
        },
        {
            "version": "1",
            "event_id": "f2",
            "run_id": "r",
            "timestamp": "2026-06-14T10:00:01Z",
            "type": "file_written",
            "scope": {},
            "payload": {"path": "README.md"},
        },
    ]
    app = build_console(MemorySource(lines))
    async with app.run_test(size=(120, 40)) as pilot:
        await _drain(app, pilot)
        await pilot.press("f")
        await pilot.pause(0.05)
        assert app.query_one(ViewRouter).current_view() == "files"
        paths = app.query_one(FileTree).paths()
        assert "src/app.py" in paths and "README.md" in paths


async def test_public_safe_default_redacts_and_opt_out_reveals() -> None:
    safe = build_console(_source())
    async with safe.run_test(size=(120, 40)) as pilot:
        await _drain(safe, pilot)
        rows = evidence_view()(safe.store.snapshot).rows
        workdir = next(r for r in rows if r.key == "workdir")
        assert "run-42" not in workdir.value  # redacted by default

    unsafe = build_console(_source(), public_safe=False)
    async with unsafe.run_test(size=(120, 40)) as pilot:
        await _drain(unsafe, pilot)
        rows = evidence_view(public_safe=False)(unsafe.store.snapshot).rows
        workdir = next(r for r in rows if r.key == "workdir")
        assert "run-42" in workdir.value  # full value shown
