"""SC-003: the UI stays responsive while a large stream ingests quickly.

1,000+ events at >=100 events/second: rendering coalesces (no unbounded
queue), input is still accepted mid-stream, and the final state is complete.
"""

import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from textual.app import ComposeResult

from intui.app import IntuiApp
from intui.events import Event, JsonlReplaySource, Scope, StreamState, write_recording
from intui.state import Snapshot, Store, compose_reducers
from intui.viewmodels import selector
from intui.widgets import BoundWidget

N_EVENTS = 1200


def make_recording(path: Path) -> None:
    write_recording(
        path,
        [
            Event(
                version="1",
                event_id=f"e{i:05d}",
                run_id="run-load",
                timestamp=datetime(2026, 6, 12, tzinfo=UTC),
                type="tick",
                scope=Scope(),
                payload={"n": i},
            )
            for i in range(N_EVENTS)
        ],
    )


def count_reducer(count: int, event: Event) -> int:
    return count + 1 if event.type == "tick" else count


@selector
def count_vm(snapshot: Snapshot) -> int:
    return snapshot.slice("count")


class CountingWidget(BoundWidget):
    def __init__(self, sel: Any, **kwargs: Any) -> None:
        super().__init__(sel, **kwargs)
        self.render_count = 0

    def render_view(self, vm: int) -> str:
        self.render_count += 1
        return str(vm)


class LoadApp(IntuiApp):
    BINDINGS = [("space", "mark", "Mark")]

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.widget = CountingWidget(count_vm)
        self.marks: list[int] = []

    def compose(self) -> ComposeResult:
        yield self.widget

    def action_mark(self) -> None:
        self.marks.append(self.store.snapshot.slice("count"))


async def test_ui_responsive_during_fast_large_replay(tmp_path: Path) -> None:
    recording = tmp_path / "load.jsonl"
    make_recording(recording)

    store = Store(compose_reducers(count=(count_reducer, 0)))
    # rate=2000 events/sec: well above the 100/sec SC-003 floor.
    app = LoadApp(store=store, source=JsonlReplaySource(recording, rate=2000.0))

    start = time.monotonic()
    async with app.run_test() as pilot:
        # Press a key mid-stream: input must be accepted while ingesting.
        await pilot.pause(0.2)
        await pilot.press("space")
        # Wait for the stream to finish.
        while store.snapshot.health.state is StreamState.LIVE:
            await pilot.pause(0.1)
            assert time.monotonic() - start < 60, "replay did not finish in time"
        await pilot.pause()

    assert store.snapshot.slice("count") == N_EVENTS
    assert app.widget.render_count >= 1
    # Coalescing: renders are far fewer than events (no unbounded queue).
    assert app.widget.render_count < N_EVENTS / 4, app.widget.render_count
    # The mid-stream key press was processed while events were flowing.
    assert len(app.marks) == 1
    assert 0 < app.marks[0] < N_EVENTS
