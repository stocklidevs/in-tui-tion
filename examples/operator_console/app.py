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
    ActivityStrip,
    CommandBar,
    ConversationLog,
    DiffViewer,
    EvidencePanel,
    LanesPanel,
    ModeStrip,
    PromptInput,
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
    prompt_message_event,
    taskboard_slice,
    tree_view,
)
from intui.state import Snapshot, Store, compose_reducers
from intui.viewmodels import selector

RECORDING = Path(__file__).parent / "recording.jsonl"
MODES = ("Plan", "Build", "Inspect", "Review")
MODE_KEYS = {"1": "Plan", "2": "Build", "3": "Inspect", "4": "Review"}


def run_status_reducer(status: str, event: Event) -> str:
    """Map run + synthetic events to R6 activity states for the KITT strip."""
    if event.type == "activity_set":
        return str(event.payload["state"])
    if event.type in {"run_started", "task_started", "subagent_started"}:
        return "thinking"
    if event.type == "task_blocked":
        return "waiting"
    if event.type == "gate_started":
        return "verifying"
    if event.type == "run_failed":
        return "failure"
    if event.type == "run_completed":
        return "passed"
    return status


@selector
def activity_state(snapshot: Snapshot) -> str:
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
    ActivityStrip { dock: top; height: 1; padding: 0 1; background: $panel; }
    ModeStrip { dock: top; padding: 0 1; background: $panel; }
    #body { height: 1fr; }
    #conversation-col { width: 38; border-right: solid $panel; }
    #mode-content { width: 1fr; padding: 0 1; }
    .col-title { text-style: bold; color: $text-muted; }
    EvidencePanel { height: auto; max-height: 50%; }
    PromptInput { dock: bottom; }
    CommandBar { dock: bottom; background: $panel; }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        yield ActivityStrip(activity_state)
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
        yield PromptInput()
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

    def _emit(self, type_: str, **payload: object) -> None:
        self.store.ingest(
            Event(
                version="1",
                event_id=f"{type_}-{datetime.now(tz=UTC).timestamp()}",
                run_id="run-console",
                timestamp=datetime.now(tz=UTC),
                type=type_,
                scope=Scope(),
                payload=payload,
            )
        )

    async def handle_intent(self, intent: Intent) -> None:
        if intent.name == "switch_mode":
            self._emit("mode_changed", mode=intent.payload["mode"])
            return
        if intent.name == "open_palette":
            self.open_command_palette(command_registry())
            return
        if intent.name == "prompt_submitted":
            self._handle_prompt(str(intent.payload["text"]))
            return
        self.notify(f"intent: {intent.name}", timeout=2.0)

    def _handle_prompt(self, text: str) -> None:
        # The full loop: user message -> "thinking" activity -> scripted reply.
        # (No live agent yet; only the reply is simulated.)
        self.store.ingest(prompt_message_event(text, run_id="run-console"))
        self._emit("activity_set", state="thinking")
        reply = f"Acknowledged: “{text}”. (No live agent wired yet — this is a scripted reply.)"
        self.set_timer(1.2, lambda: self._finish_prompt(reply))

    def _finish_prompt(self, reply: str) -> None:
        self._emit("message_added", role="agent", text=reply)
        self._emit("activity_set", state="passed")


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
