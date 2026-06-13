"""mission_control: task chip, task tree, and parallel lanes over one replay.

Replays a recorded run with two overlapping workers. Everything on screen
derives from the standard event vocabulary through the kit's ready-made
reduction — the app defines no custom reducers at all.
"""

from __future__ import annotations

from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Footer, Header, Label

from intui.app import IntuiApp
from intui.events import JsonlReplaySource
from intui.kit import LanesPanel, TaskCounterChip, TaskTree
from intui.kit.state import chip_view, lanes_view, taskboard_slice, tree_view
from intui.state import Store, compose_reducers

RECORDING = Path(__file__).parent / "recording.jsonl"


class MissionControlApp(IntuiApp):
    TITLE = "in-TUI-tion · mission_control"
    BINDINGS = [("q", "quit", "Quit")]
    CSS = """
    TaskCounterChip { dock: top; padding: 0 1; background: $panel; }
    #columns { height: 1fr; }
    #tasks-col { width: 2fr; border-right: solid $panel; padding: 0 1; }
    #lanes-col { width: 1fr; padding: 0 1; }
    .col-title { text-style: bold; color: $text-muted; }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        yield TaskCounterChip(chip_view())
        with Horizontal(id="columns"):
            with Vertical(id="tasks-col"):
                yield Label("Tasks", classes="col-title")
                yield TaskTree(tree_view())
            with Vertical(id="lanes-col"):
                yield Label("Workers", classes="col-title")
                yield LanesPanel(lanes_view())
        yield Footer()


def build_app(events_per_second: float = 3.0) -> MissionControlApp:
    store = Store(compose_reducers(taskboard=taskboard_slice()))
    return MissionControlApp(
        store=store, source=JsonlReplaySource(RECORDING, rate=events_per_second)
    )


if __name__ == "__main__":
    build_app().run()
