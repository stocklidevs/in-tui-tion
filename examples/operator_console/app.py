"""operator_console: the flagship agentic operator console (R13, R1).

Composes the whole kit — conversation, task chip, task tree, parallel lanes,
activity signal, command surfaces, diff viewer, evidence panel — across four
modes (Plan/Build/Inspect/Review), driven by one recorded run. Mode switching
flows intent -> mode_changed event -> state, the same loop as everything else.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Horizontal, VerticalScroll
from textual.widgets import ContentSwitcher, Footer, Header, Label

from intui.actions import Intent
from intui.app import IntuiApp
from intui.events import Event, JsonlReplaySource, Scope
from intui.kit import (
    CommandBar,
    ConversationLog,
    DiffViewer,
    EvidencePanel,
    LanesPanel,
    ModeStrip,
    TaskCounterChip,
    TaskTree,
)
from intui.kit.state import (
    Command,
    CommandRegistry,
    artifacts_slice,
    chip_view,
    conversation_slice,
    conversation_view,
    diff_view,
    evidence_view,
    lanes_view,
    mode_slice,
    mode_view,
    taskboard_slice,
    tree_view,
)
from intui.state import Snapshot, Store, compose_reducers
from intui.theming import MotionMode, StatusStyle
from intui.viewmodels import selector
from intui.widgets import Signal

RECORDING = Path(__file__).parent / "recording.jsonl"
MODES = ("Plan", "Build", "Inspect", "Review")
MODE_KEYS = {"1": "Plan", "2": "Build", "3": "Inspect", "4": "Review"}

RUN_SIGNAL_STYLES = {
    "running": StatusStyle(color="thinking", motion=MotionMode.SWOOSH, glyph="»", label="working"),
    "verifying": StatusStyle(
        color="verifying", motion=MotionMode.SWOOSH, glyph="≈", label="verifying"
    ),
    "passed": StatusStyle(color="success", motion=MotionMode.STEADY, glyph="✔", label="passed"),
    "blocked": StatusStyle(color="waiting", motion=MotionMode.PULSE, glyph="▲", label="blocked"),
    "failed": StatusStyle(color="failure", motion=MotionMode.STROBE, glyph="✘", label="failed"),
    "idle": StatusStyle(color="muted", motion=MotionMode.STEADY, glyph="·", label="idle"),
}


def run_status_reducer(status: str, event: Event) -> str:
    if event.type in {"run_started", "task_started", "subagent_started"}:
        return "running"
    if event.type == "task_blocked":
        return "blocked"
    if event.type == "gate_started":
        return "verifying"
    if event.type in {"run_completed"}:
        return "passed"
    return status


@selector
def run_signal_status(snapshot: Snapshot) -> str:
    return snapshot.slice("run_status")


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


class OperatorConsole(IntuiApp):
    TITLE = "in-TUI-tion · operator console"
    BINDINGS = [("q", "quit", "Quit"), ("ctrl+p", "palette", "Commands")]
    CSS = """
    ModeStrip { dock: top; padding: 0 1; background: $panel; }
    #body { height: 1fr; }
    #conversation-col { width: 38; border-right: solid $panel; }
    #mode-content { width: 1fr; padding: 0 1; }
    .col-title { text-style: bold; color: $text-muted; }
    Signal { dock: top; height: 1; padding: 0 1; }
    EvidencePanel { height: auto; max-height: 50%; }
    CommandBar { dock: bottom; background: $panel; }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        yield ModeStrip(mode_view(), keys=MODE_KEYS)
        with Horizontal(id="body"):
            with VerticalScroll(id="conversation-col"):
                yield Label("Conversation", classes="col-title")
                yield ConversationLog(conversation_view())
            with ContentSwitcher(initial="pane-Plan", id="mode-content"):
                with VerticalScroll(id="pane-Plan"):
                    yield Label("Plan", classes="col-title")
                    yield TaskCounterChip(chip_view())
                with VerticalScroll(id="pane-Build"):
                    yield Signal(run_signal_status, RUN_SIGNAL_STYLES)
                    yield TaskCounterChip(chip_view())
                    yield Label("Tasks", classes="col-title")
                    yield TaskTree(tree_view())
                    yield Label("Workers", classes="col-title")
                    yield LanesPanel(lanes_view())
                with VerticalScroll(id="pane-Inspect"):
                    yield Label("Evidence", classes="col-title")
                    yield EvidencePanel(evidence_view())
                    yield Label("Diff (public-safe)", classes="col-title")
                    yield DiffViewer(diff_view())
                with VerticalScroll(id="pane-Review"):
                    yield Label("Evidence", classes="col-title")
                    yield EvidencePanel(evidence_view())
        yield CommandBar(command_registry())
        yield Footer()

    def on_mount(self) -> None:
        super().on_mount()
        self.store.subscribe(self._sync_mode_pane)

    def _sync_mode_pane(self, snapshot: Snapshot) -> None:
        current = snapshot.slice("modes").current
        switcher = self.query_one("#mode-content", ContentSwitcher)
        pane = f"pane-{current}"
        if switcher.current != pane:
            switcher.current = pane

    def action_palette(self) -> None:
        self.open_command_palette(command_registry())

    async def handle_intent(self, intent: Intent) -> None:
        if intent.name == "switch_mode":
            self.store.ingest(
                Event(
                    version="1",
                    event_id=f"switch-{datetime.now(tz=UTC).timestamp()}",
                    run_id="run-console",
                    timestamp=datetime.now(tz=UTC),
                    type="mode_changed",
                    scope=Scope(),
                    payload={"mode": intent.payload["mode"]},
                )
            )
            return
        if intent.name == "open_palette":
            self.open_command_palette(command_registry())
            return
        self.notify(f"intent: {intent.name}", timeout=2.0)


def build_app(events_per_second: float = 4.0) -> OperatorConsole:
    store = Store(
        compose_reducers(
            modes=mode_slice(MODES),
            conversation=conversation_slice(),
            taskboard=taskboard_slice(),
            artifacts=artifacts_slice(),
            run_status=(run_status_reducer, "idle"),
        )
    )
    return OperatorConsole(
        store=store, source=JsonlReplaySource(RECORDING, rate=events_per_second)
    )


if __name__ == "__main__":
    build_app().run()
