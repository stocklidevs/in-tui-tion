"""mission_control: task chip, task tree, parallel lanes, and command surfaces.

Replays a recorded run with two overlapping workers. The task views derive
from the standard event vocabulary through the kit's ready-made reduction; the
command bar and palette drive a shared command registry, emitting intents
(one of them risky) through the app's confirmation flow.
"""

from __future__ import annotations

from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Footer, Header, Label

from intui.actions import Intent
from intui.app import IntuiApp
from intui.events import JsonlReplaySource
from intui.kit import CommandBar, TaskCounterChip, TaskTree, LanesPanel
from intui.kit.state import (
    Command,
    CommandRegistry,
    chip_view,
    lanes_view,
    taskboard_slice,
    tree_view,
)
from intui.state import Store, compose_reducers

RECORDING = Path(__file__).parent / "recording.jsonl"


def command_registry() -> CommandRegistry:
    return CommandRegistry(
        [
            Command("approve", "Approve", Intent("approve"), key="a"),
            Command("diff", "Diff", Intent("open_diff"), key="d"),
            Command("evidence", "Evidence", Intent("open_evidence"), key="e"),
            Command("cancel", "Cancel run", Intent("cancel", risky=True), key="x"),
            Command("palette", "More", Intent("open_palette"), key="p"),
        ]
    )


class MissionControlApp(IntuiApp):
    TITLE = "in-TUI-tion · mission_control"
    BINDINGS = [("q", "quit", "Quit")]
    CSS = """
    TaskCounterChip { dock: top; padding: 0 1; background: $panel; }
    #columns { height: 1fr; }
    #tasks-col { width: 2fr; border-right: solid $panel; padding: 0 1; }
    #lanes-col { width: 1fr; padding: 0 1; }
    .col-title { text-style: bold; color: $text-muted; }
    CommandBar { dock: bottom; background: $panel; }
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
        yield CommandBar(command_registry())
        yield Footer()

    async def handle_intent(self, intent: Intent) -> None:
        # The example has no real backend; surface the intent as a toast so
        # invocation (and risky confirmation) is visible.
        self.notify(f"intent: {intent.name}", timeout=2.0)


def build_app(events_per_second: float = 3.0) -> MissionControlApp:
    store = Store(compose_reducers(taskboard=taskboard_slice()))
    return MissionControlApp(
        store=store, source=JsonlReplaySource(RECORDING, rate=events_per_second)
    )


if __name__ == "__main__":
    build_app().run()
