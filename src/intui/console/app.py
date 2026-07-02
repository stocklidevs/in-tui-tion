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
from pathlib import Path

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, VerticalScroll
from textual.widget import Widget
from textual.widgets import Footer, Header, Label, Static

from intui.actions import Intent
from intui.app import IntuiApp
from intui.events import Event, EventSource, Scope, write_recording
from intui.kit import (
    ActivityStrip,
    CommandBar,
    ConversationLog,
    DiffViewer,
    EvidencePanel,
    FileTree,
    LanesPanel,
    MetricsPanel,
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
    metrics_slice,
    metrics_view,
    run_status_slice,
    select_view_intent,
    taskboard_slice,
    tree_view,
    view_router_view,
    view_slice,
    workspace_slice,
)
from intui.state import Snapshot, Store, Timeline, compose_reducers
from intui.viewmodels import selector

VIEWS = ("tasks", "lanes", "files", "diff", "evidence", "metrics")


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
            Command("view_metrics", "Metrics", select_view_intent("metrics"), key="m"),
            Command("palette", "More", Intent("open_palette"), key="p"),
        ]
    )


class ConsoleApp(IntuiApp):
    """A zero-config console over the canonical event vocabulary."""

    TITLE = "in-TUI-tion · console"
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("t", "open_panel('tasks')", "Tasks"),
        ("l", "open_panel('lanes')", "Lanes"),
        ("f", "open_panel('files')", "Files"),
        ("e", "open_panel('evidence')", "Evidence"),
        ("m", "open_panel('metrics')", "Metrics"),
        ("ctrl+p", "palette", "Commands"),
        ("ctrl+s", "record", "Save run"),
        ("space", "scrub_toggle", "Pause/Live"),
        Binding("comma", "scrub_back", "Step back", show=False),
        Binding("full_stop", "scrub_forward", "Step fwd", show=False),
        Binding("home", "scrub_start", "To start", show=False),
        Binding("end", "scrub_live", "To live", show=False),
    ]
    CSS = """
    /* Header and Footer self-dock; everything else flows top-to-bottom. */
    ActivityStrip { height: 1; padding: 0 1; background: $panel; }
    #body { height: 1fr; }
    #conversation-col { width: 38; border-right: solid $panel; }
    ViewRouter { width: 1fr; padding: 0 1; }
    .col-title { text-style: bold; color: $text-muted; }
    EvidencePanel { height: auto; }
    CommandBar { height: 1; background: $panel; }
    #scrub-bar { height: 1; padding: 0 1; color: $text-muted; }
    """

    def __init__(
        self,
        *,
        public_safe: bool = True,
        sweep_seconds: float = 1.6,
        file_actions: bool = False,
        **kwargs: object,
    ) -> None:
        super().__init__(**kwargs)  # type: ignore[arg-type]
        self._public_safe = public_safe
        self._sweep_seconds = sweep_seconds
        self._file_actions = file_actions
        self._timeline = Timeline()  # starts live (follow the end)

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
                    "metrics": MetricsPanel(metrics_view(public_safe=self._public_safe)),
                },
            )
        yield Static(id="scrub-bar")
        yield CommandBar(_command_registry())
        yield Footer()

    def on_mount(self) -> None:
        super().on_mount()
        # Keep the scrub status fresh as events arrive (esp. the total while
        # paused); the held view itself stays frozen via the bridge.
        self.store.subscribe(lambda _snapshot: self._refresh_scrub_bar())
        self._refresh_scrub_bar()

    def action_palette(self) -> None:
        self.open_command_palette(_command_registry())

    # --- Panel overlays ------------------------------------------------------

    def action_open_panel(self, name: str) -> None:
        """Open a browsable panel as a modal overlay over the timeline."""
        from intui.console.overlays import PanelOverlay

        panel = self._panel_for(name)
        if panel is None:
            return
        self.push_screen(PanelOverlay(name, panel))

    def _panel_for(self, name: str) -> Widget | None:
        ps = self._public_safe
        if name == "files":
            return FileTree(file_tree_view(public_safe=ps))
        if name == "metrics":
            return MetricsPanel(metrics_view(public_safe=ps))
        if name == "lanes":
            return LanesPanel(lanes_view())
        if name == "evidence":
            return EvidencePanel(evidence_view(public_safe=ps))
        if name == "tasks":
            return VerticalScroll(
                TaskCounterChip(chip_view()),
                TaskTree(tree_view()),
            )
        return None

    # --- Time-travel scrubber -----------------------------------------------

    def _apply_scrub(self) -> None:
        total = len(self.store.events)
        if self._timeline.live:
            self.bridge.release()
        else:
            self.bridge.hold(self.store.snapshot_at(self._timeline.position(total)))
        self._refresh_scrub_bar()

    def _refresh_scrub_bar(self) -> None:
        try:
            bar = self.query_one("#scrub-bar", Static)
        except Exception:  # noqa: BLE001 - not mounted yet
            return
        bar.update(self._timeline.label(len(self.store.events)))

    def action_scrub_toggle(self) -> None:
        self._timeline = self._timeline.toggle(len(self.store.events))
        self._apply_scrub()

    def action_scrub_back(self) -> None:
        self._timeline = self._timeline.step(-1, len(self.store.events))
        self._apply_scrub()

    def action_scrub_forward(self) -> None:
        self._timeline = self._timeline.step(1, len(self.store.events))
        self._apply_scrub()

    def action_scrub_start(self) -> None:
        self._timeline = self._timeline.to_start()
        self._apply_scrub()

    def action_scrub_live(self) -> None:
        self._timeline = self._timeline.to_end()
        self._apply_scrub()

    def _record_path(self) -> Path:
        stamp = datetime.now(tz=UTC).strftime("%Y%m%d-%H%M%S")
        return Path(f"intui-recording-{stamp}.jsonl")

    def action_record(self) -> None:
        """Save the run seen so far to a canonical, replayable ``.jsonl``.

        Writes the store's *accepted* events (canonical envelopes — no wrapper),
        so the file replays with ``intui watch <file>`` and no adapter. A write
        failure is reported, never fatal.
        """
        path = self._record_path()
        try:
            write_recording(path, self.store.events)
        except OSError as exc:
            self.notify(f"could not save: {exc}", severity="error", timeout=4.0)
            return
        self.notify(f"saved {len(self.store.events)} events → {path}", timeout=4.0)

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
        if intent.name in ("copy_path", "open_file", "delete_file"):
            self._handle_file_action(intent)
            return
        self.notify(f"intent: {intent.name}", timeout=2.0)

    def _handle_file_action(self, intent: Intent) -> None:
        """Fulfill a file-action intent.

        ``copy_path`` (non-destructive) is handled for real. ``open_file`` and
        ``delete_file`` only act when the app was built with
        ``file_actions=True`` — a default console reports them but never mutates
        the filesystem (Principle III / safe-by-default).
        """
        path = str(intent.payload.get("path", ""))
        if intent.name == "copy_path":
            self.copy_to_clipboard(path)
            self.notify(f"copied: {path}", timeout=2.0)
            return
        if not self._file_actions:
            self.notify(f"{intent.name}: {path} (read-only; file_actions=False)", timeout=3.0)
            return
        from intui.actions.files import delete_path, open_in_editor

        if intent.name == "open_file":
            open_in_editor(path)
            self.notify(f"opened: {path}", timeout=2.0)
        elif intent.name == "delete_file":  # already confirmed (risky)
            delete_path(path)
            self._emit("file_removed", path=path)  # reflect it back into the tree
            self.notify(f"deleted: {path}", timeout=2.0)


def build_console(
    source: EventSource,
    *,
    public_safe: bool = True,
    sweep_seconds: float = 1.6,
    file_actions: bool = False,
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
            metrics=metrics_slice(),
            run_status=run_status_slice(),
        )
    )
    return ConsoleApp(
        store=store,
        source=source,
        public_safe=public_safe,
        sweep_seconds=sweep_seconds,
        file_actions=file_actions,
    )
