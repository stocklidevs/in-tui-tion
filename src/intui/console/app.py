"""ConsoleApp: the batteries-included, zero-config console (R-runner).

Point it at any canonical event stream and get a console — no application
reducers, no widgets to wire. A read-mostly viewer: a signature KITT activity
strip, a persistent conversation, a routable central view
(tasks / lanes / diff / evidence), and a command bar. Public-safe by default.

The full interactive operator console (modes, prompt, scripted replies) stays
the flagship *example*; this is the generic substrate.
"""

from __future__ import annotations

from datetime import UTC, datetime

from textual.app import ComposeResult
from textual.containers import Horizontal, VerticalScroll
from textual.widgets import Footer, Header, Label

from intui.actions import Intent
from intui.app import IntuiApp
from intui.events import Event, EventSource, Scope
from intui.kit import (
    ActivityStrip,
    CommandBar,
    ConversationLog,
    DiffViewer,
    EvidencePanel,
    FileTree,
    LanesPanel,
    TaskCounterChip,
    TaskTree,
    ViewRouter,
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
    file_tree_view,
    lanes_view,
    run_status_slice,
    select_view_intent,
    taskboard_slice,
    tree_view,
    view_router_view,
    view_slice,
    workspace_slice,
)
from intui.state import Snapshot, Store, compose_reducers
from intui.viewmodels import selector

VIEWS = ("tasks", "lanes", "files", "diff", "evidence")


@selector
def _activity_state(snapshot: Snapshot) -> str:
    return str(snapshot.slice("run_status"))


def _command_registry() -> CommandRegistry:
    return CommandRegistry(
        [
            Command("view_tasks", "Tasks", select_view_intent("tasks"), key="t"),
            Command("view_lanes", "Lanes", select_view_intent("lanes"), key="l"),
            Command("view_files", "Files", select_view_intent("files"), key="f"),
            Command("view_diff", "Diff", select_view_intent("diff"), key="d"),
            Command("view_evidence", "Evidence", select_view_intent("evidence"), key="e"),
            Command("palette", "More", Intent("open_palette"), key="p"),
        ]
    )


class ConsoleApp(IntuiApp):
    """A zero-config console over the canonical event vocabulary."""

    TITLE = "in-TUI-tion · console"
    BINDINGS = [("q", "quit", "Quit"), ("ctrl+p", "palette", "Commands")]
    CSS = """
    /* Header and Footer self-dock; everything else flows top-to-bottom. */
    ActivityStrip { height: 1; padding: 0 1; background: $panel; }
    #body { height: 1fr; }
    #conversation-col { width: 38; border-right: solid $panel; }
    ViewRouter { width: 1fr; padding: 0 1; }
    .col-title { text-style: bold; color: $text-muted; }
    EvidencePanel { height: auto; }
    CommandBar { height: 1; background: $panel; }
    """

    def __init__(
        self, *, public_safe: bool = True, sweep_seconds: float = 1.6, **kwargs: object
    ) -> None:
        super().__init__(**kwargs)  # type: ignore[arg-type]
        self._public_safe = public_safe
        self._sweep_seconds = sweep_seconds

    def compose(self) -> ComposeResult:
        yield Header()
        yield ActivityStrip(_activity_state, swoosh_glow=6, sweep_seconds=self._sweep_seconds)
        with Horizontal(id="body"):
            with VerticalScroll(id="conversation-col"):
                yield Label("Conversation", classes="col-title")
                yield ConversationLog(conversation_view())
            yield ViewRouter(
                view_router_view(),
                views={
                    "tasks": VerticalScroll(
                        TaskCounterChip(chip_view()),
                        Label("Tasks", classes="col-title"),
                        TaskTree(tree_view()),
                    ),
                    "lanes": LanesPanel(lanes_view()),
                    "files": FileTree(file_tree_view(public_safe=self._public_safe)),
                    "diff": DiffViewer(diff_view(public_safe=self._public_safe)),
                    "evidence": EvidencePanel(evidence_view(public_safe=self._public_safe)),
                },
            )
        yield CommandBar(_command_registry())
        yield Footer()

    def action_palette(self) -> None:
        self.open_command_palette(_command_registry())

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
        if intent.name == "select_view":
            self._emit("view_selected", view=intent.payload["view"])
            return
        if intent.name == "open_palette":
            self.open_command_palette(_command_registry())
            return
        self.notify(f"intent: {intent.name}", timeout=2.0)


def build_console(
    source: EventSource,
    *,
    public_safe: bool = True,
    sweep_seconds: float = 1.6,
) -> ConsoleApp:
    """Build a :class:`ConsoleApp` over ``source`` with the canonical slices.

    No application reducers required — the bundled taskboard / artifacts /
    conversation / view-router / run-status slices reduce the canonical stream.
    """
    store = Store(
        compose_reducers(
            views=view_slice(VIEWS, "tasks"),
            conversation=conversation_slice(),
            taskboard=taskboard_slice(),
            artifacts=artifacts_slice(),
            workspace=workspace_slice(),
            run_status=run_status_slice(),
        )
    )
    return ConsoleApp(
        store=store, source=source, public_safe=public_safe, sweep_seconds=sweep_seconds
    )
