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
from intui.kit import (
    CommandBar,
    DiffViewer,
    EvidencePanel,
    LanesPanel,
    TaskCounterChip,
    TaskTree,
)
from intui.kit.state import (
    Command,
    CommandRegistry,
    artifacts_slice,
    chip_view,
    diff_view,
    evidence_view,
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
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("ctrl+p", "palette", "Commands"),
    ]
    CSS = """
    TaskCounterChip { dock: top; padding: 0 1; background: $panel; }
    #columns { height: 1fr; }
    #tasks-col { width: 1fr; border-right: solid $panel; padding: 0 1; }
    #lanes-col { width: 1fr; border-right: solid $panel; padding: 0 1; }
    #inspect-col { width: 2fr; padding: 0 1; }
    .col-title { text-style: bold; color: $text-muted; }
    EvidencePanel { height: auto; max-height: 50%; }
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
            with Vertical(id="inspect-col"):
                yield Label("Evidence", classes="col-title")
                yield EvidencePanel(evidence_view())
                yield Label("Diff (public-safe)", classes="col-title")
                yield DiffViewer(diff_view())
        yield CommandBar(command_registry())
        yield Footer()

    def action_palette(self) -> None:
        self.open_command_palette(command_registry())

    async def handle_intent(self, intent: Intent) -> None:
        # The "More" command opens the palette; everything else is surfaced as
        # a toast so invocation (and risky confirmation) is visible.
        if intent.name == "open_palette":
            self.open_command_palette(command_registry())
            return
        self.notify(f"intent: {intent.name}", timeout=2.0)


def build_app(events_per_second: float = 3.0) -> MissionControlApp:
    store = Store(compose_reducers(taskboard=taskboard_slice(), artifacts=artifacts_slice()))
    return MissionControlApp(
        store=store, source=JsonlReplaySource(RECORDING, rate=events_per_second)
    )


if __name__ == "__main__":
    build_app().run()
