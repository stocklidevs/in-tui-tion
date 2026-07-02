"""ConsoleApp: zero-config console renders a canonical stream, navigates views
by keyboard, honors public-safe, and reflects stream end — no application code."""

from __future__ import annotations

from pathlib import Path

from intui.console import build_console
from intui.events import MemorySource, NdjsonStreamSource, StreamState
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
    from intui.console import RunTimeline

    app = build_console(_source())
    async with app.run_test(size=(120, 40)) as pilot:
        await _drain(app, pilot)
        art = app.store.snapshot.slice("artifacts")
        assert art.diff is not None and len(art.diff.files) == 3
        assert art.evidence is not None
        assert len(app.store.snapshot.slice("conversation").entries) >= 5
        assert app.store.snapshot.slice("taskboard").tasks
        assert app.store.snapshot.health.state is StreamState.ENDED
        # the timeline is the primary surface and reduced the run
        timeline = app.query_one(RunTimeline)
        assert timeline.log_text().strip()
        assert "waiting for events" not in timeline.log_text()


async def test_panels_are_keyboard_navigable() -> None:
    # Browsable panels open as overlays (Esc closes); full coverage lives in
    # tests/integration/test_console_overlays.py.
    app = build_console(_source())
    async with app.run_test(size=(120, 40)) as pilot:
        await _drain(app, pilot)
        for key in ("l", "f", "e", "t", "m"):
            await pilot.press(key)
            await pilot.pause(0.05)
            assert app.screen_stack[-1].__class__.__name__ == "PanelOverlay", key
            await pilot.press("escape")
            await pilot.pause(0.05)
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
        assert app.screen_stack[-1].__class__.__name__ == "PanelOverlay"
        paths = app.screen_stack[-1].query_one(FileTree).paths()
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


# --- file actions (014) ------------------------------------------------------


def _file_stream(path: str) -> MemorySource:
    return MemorySource(
        [
            {
                "version": "1",
                "event_id": "f1",
                "run_id": "r",
                "timestamp": "2026-06-14T10:00:00Z",
                "type": "file_written",
                "scope": {},
                "payload": {"path": path, "change_type": "added"},
            }
        ]
    )


async def _select_file(app: object, pilot: object, path: str) -> None:
    from textual.widgets import Tree

    from intui.kit import FileTree

    await pilot.press("f")  # type: ignore[attr-defined]
    await pilot.pause(0.05)  # type: ignore[attr-defined]
    # query within the active overlay screen (App.query_one searches the
    # default screen, not the pushed modal)
    overlay = app.screen_stack[-1]  # type: ignore[attr-defined]
    tree = overlay.query_one(FileTree).query_one(Tree)
    tree.focus()
    await pilot.pause()  # type: ignore[attr-defined]

    def walk(node: object) -> object:
        for child in node.children:  # type: ignore[attr-defined]
            yield child
            yield from walk(child)

    node = next(n for n in walk(tree.root) if n.data == path)
    tree.move_cursor(node)
    await pilot.pause()  # type: ignore[attr-defined]


async def test_copy_path_copies_to_clipboard() -> None:
    app = build_console(_file_stream("src/app.py"))
    copied: list[str] = []
    app.copy_to_clipboard = copied.append  # type: ignore[method-assign]
    async with app.run_test(size=(100, 30)) as pilot:
        await _drain(app, pilot)
        await _select_file(app, pilot, "src/app.py")
        await pilot.press("c")
        await pilot.pause(0.05)
        assert copied == ["src/app.py"]


async def test_default_console_does_not_delete(tmp_path: Path) -> None:
    target = tmp_path / "victim.txt"
    target.write_text("keep me", encoding="utf-8")
    norm = str(target).replace("\\", "/")
    app = build_console(_file_stream(norm))  # file_actions defaults False
    async with app.run_test(size=(100, 30)) as pilot:
        await _drain(app, pilot)
        await _select_file(app, pilot, norm)
        await pilot.press("x")
        await pilot.pause(0.05)
        await pilot.press("y")  # confirm
        await pilot.pause(0.05)
        assert target.exists()  # report-only: the viewer never deleted it


async def test_file_actions_true_deletes_on_confirm(tmp_path: Path) -> None:
    target = tmp_path / "victim.txt"
    target.write_text("bye", encoding="utf-8")
    norm = str(target).replace("\\", "/")
    app = build_console(_file_stream(norm), file_actions=True)
    async with app.run_test(size=(100, 30)) as pilot:
        await _drain(app, pilot)
        await _select_file(app, pilot, norm)
        await pilot.press("x")
        await pilot.pause(0.05)
        await pilot.press("y")  # confirm
        await pilot.pause(0.1)
        assert not target.exists()  # real deletion when opted in


# --- metrics view (015) ------------------------------------------------------


async def test_metrics_view_reachable_and_shows_panel() -> None:
    from intui.kit import MetricsPanel

    lines = [
        {
            "version": "1",
            "event_id": "p1",
            "run_id": "r",
            "timestamp": "2026-06-14T10:00:00Z",
            "type": "process_started",
            "scope": {},
            "payload": {"label": "build.py"},
        },
        {
            "version": "1",
            "event_id": "p2",
            "run_id": "r",
            "timestamp": "2026-06-14T10:00:01Z",
            "type": "metric_sample",
            "scope": {},
            "payload": {"cpu_percent": 40.0, "rss_bytes": 53400000, "elapsed_ms": 1200},
        },
        {
            "version": "1",
            "event_id": "p3",
            "run_id": "r",
            "timestamp": "2026-06-14T10:00:02Z",
            "type": "process_exited",
            "scope": {},
            "status": "passed",
            "payload": {"exit_code": 0, "duration_ms": 1800},
        },
    ]
    app = build_console(MemorySource(lines))
    async with app.run_test(size=(100, 30)) as pilot:
        await _drain(app, pilot)
        await pilot.press("m")
        await pilot.pause(0.05)
        assert app.screen_stack[-1].__class__.__name__ == "PanelOverlay"
        panel = app.screen_stack[-1].query_one(MetricsPanel)
        assert panel.status() == "passed"
        assert "build.py" in panel.summary_text()


# --- record (016) ------------------------------------------------------------


def _task_stream() -> MemorySource:
    return MemorySource(
        [
            {
                "version": "1",
                "event_id": "t1",
                "run_id": "r",
                "timestamp": "2026-06-14T10:00:00Z",
                "type": "task_started",
                "scope": {"task_id": "build"},
                "payload": {"name": "Build"},
            },
            {
                "version": "1",
                "event_id": "t2",
                "run_id": "r",
                "timestamp": "2026-06-14T10:00:01Z",
                "type": "task_completed",
                "scope": {"task_id": "build"},
                "status": "passed",
            },
        ]
    )


async def test_record_writes_replayable_canonical_file(tmp_path: Path) -> None:
    from intui.events import read_recording

    out = tmp_path / "rec.jsonl"
    app = build_console(_task_stream())
    app._record_path = lambda: out  # type: ignore[method-assign]
    async with app.run_test(size=(100, 30)) as pilot:
        await _drain(app, pilot)
        await pilot.press("ctrl+s")
        await pilot.pause(0.05)
    assert out.is_file()
    events = read_recording(out)
    assert [e.event_id for e in events] == ["t1", "t2"]

    # round-trip: replay the recording into a fresh console -> same task state
    replay = build_console(NdjsonStreamSource(out))
    async with replay.run_test(size=(100, 30)) as pilot:
        await _drain(replay, pilot)
        assert {t.task_id for t in replay.store.snapshot.slice("taskboard").tasks.values()} == {
            "build"
        }


async def test_record_of_adapted_source_is_canonical(tmp_path: Path) -> None:
    from intui.adapters import IntentForgeSource
    from intui.events import read_recording

    out = tmp_path / "rec.jsonl"
    if_lines = [
        '{"type":"run_trace_event","event":{"sequence":1,"name":"case_started",'
        '"payload":{"case_id":"c1"}}}'
    ]
    app = build_console(IntentForgeSource(if_lines))
    app._record_path = lambda: out  # type: ignore[method-assign]
    async with app.run_test(size=(100, 30)) as pilot:
        await _drain(app, pilot)
        await pilot.press("ctrl+s")
        await pilot.pause(0.05)
    events = read_recording(out)  # canonical (no run_trace_event wrapper)
    assert events and events[0].type == "task_started"


# --- time-travel scrubber (017) ---------------------------------------------


def _tasks_stream(n: int) -> MemorySource:
    return MemorySource(
        [
            {
                "version": "1",
                "event_id": f"e{i}",
                "run_id": "r",
                "timestamp": "2026-06-14T10:00:00Z",
                "type": "task_started",
                "scope": {"task_id": f"t{i}"},
                "payload": {"name": f"task {i}"},
            }
            for i in range(n)
        ]
    )


async def test_scrub_steps_through_history() -> None:
    from intui.kit import TaskCounterChip

    app = build_console(_tasks_stream(4))
    async with app.run_test(size=(120, 40)) as pilot:
        await _drain(app, pilot)
        # scrub while the tasks overlay is open (the chip lives there now)
        await pilot.press("t")
        await pilot.pause(0.05)
        chip = app.screen_stack[-1].query_one(TaskCounterChip)
        assert "/ 4 tasks" in chip.header_text()

        app.action_scrub_toggle()  # pause at 4
        await pilot.pause(0.05)
        assert "/ 4 tasks" in chip.header_text()

        app.action_scrub_back()  # -> 3
        await pilot.pause(0.05)
        assert "/ 3 tasks" in chip.header_text()
        assert app._timeline.position(len(app.store.events)) == 3

        app.action_scrub_start()  # -> 0
        await pilot.pause(0.05)
        assert "no tasks" in chip.header_text()

        app.action_scrub_live()  # -> latest
        await pilot.pause(0.05)
        assert "/ 4 tasks" in chip.header_text()


async def test_scrub_holds_while_live_grows() -> None:
    from datetime import UTC, datetime

    from intui.events import Event, Scope
    from intui.kit import TaskCounterChip

    app = build_console(_tasks_stream(2))
    async with app.run_test(size=(120, 40)) as pilot:
        await _drain(app, pilot)
        await pilot.press("t")  # the chip lives in the tasks overlay now
        await pilot.pause(0.05)
        chip = app.screen_stack[-1].query_one(TaskCounterChip)

        app.action_scrub_back()  # pause at 1
        await pilot.pause(0.05)
        assert "/ 1 tasks" in chip.header_text()

        # more events arrive after we paused (simulate a growing live stream)
        for i in range(2, 5):
            app.store.ingest(
                Event(
                    version="1",
                    event_id=f"x{i}",
                    run_id="r",
                    timestamp=datetime(2026, 6, 14, tzinfo=UTC),
                    type="task_started",
                    scope=Scope(task_id=f"t{i}"),
                )
            )
        await pilot.pause(0.05)
        assert "/ 1 tasks" in chip.header_text()  # held view stays frozen
        assert len(app.store.events) == 5 and app._timeline.position(5) == 1

        app.action_scrub_live()  # resume -> latest (5)
        await pilot.pause(0.05)
        assert "/ 5 tasks" in chip.header_text()
