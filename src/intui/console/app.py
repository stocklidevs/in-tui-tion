"""ConsoleApp: the batteries-included, zero-config console (R-runner).

Point it at any canonical event stream and get a console — no application
reducers, no widgets to wire. The run itself is the interface: a single-column
timeline of the stream (messages, task results, failure callouts) under the
signature KITT activity strip, with a floor-pinned prompt for slash commands.
Diffs unfold inline (``d`` / ``/diff``); the browsable panels (tasks / lanes /
files / evidence / metrics) open as modal overlays (keys or ``/name``, Esc
closes). Public-safe by default.

The full interactive operator console (modes, scripted replies) stays the
flagship *example*; this is the generic substrate.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import VerticalScroll
from textual.widget import Widget
from textual.widgets import Footer, Header, Static

from intui.actions import Intent
from intui.app import IntuiApp
from intui.events import Event, EventSource, Scope, write_recording
from intui.kit import (
    ActivityStrip,
    DiffViewer,
    EvidencePanel,
    FileTree,
    LanesPanel,
    MetricsPanel,
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
    diff_view,
    evidence_view,
    file_tree_view,
    lanes_view,
    metrics_slice,
    metrics_view,
    prompt_message_event,
    run_status_slice,
    run_timeline_view,
    taskboard_slice,
    timeline_slice,
    tree_view,
    workspace_slice,
)
from intui.state import Snapshot, Store, Timeline, compose_reducers
from intui.viewmodels import selector

PANELS = ("tasks", "lanes", "files", "evidence", "metrics")


@selector
def _activity_state(snapshot: Snapshot) -> str:
    return str(snapshot.slice("run_status"))


def _open_panel_intent(name: str) -> Intent:
    return Intent("open_panel", {"name": name})


def _command_registry() -> CommandRegistry:
    # Feeds the command palette (ctrl+p); the same actions have key BINDINGS
    # and /slash forms on the prompt.
    return CommandRegistry(
        [
            Command("panel_tasks", "Tasks", _open_panel_intent("tasks"), key="t"),
            Command("panel_lanes", "Lanes", _open_panel_intent("lanes"), key="l"),
            Command("panel_files", "Files", _open_panel_intent("files"), key="f"),
            Command("toggle_diff", "Diff", Intent("toggle_diff"), key="d"),
            Command("panel_evidence", "Evidence", _open_panel_intent("evidence"), key="e"),
            Command("panel_metrics", "Metrics", _open_panel_intent("metrics"), key="m"),
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
        ("d", "toggle_diff", "Diff"),
        ("slash", "focus_prompt", "Prompt"),
        ("ctrl+p", "palette", "Commands"),
        ("ctrl+s", "record", "Save run"),
        ("space", "scrub_toggle", "Pause/Live"),
        Binding("comma", "scrub_back", "Step back", show=False),
        Binding("full_stop", "scrub_forward", "Step fwd", show=False),
        Binding("home", "scrub_start", "To start", show=False),
        Binding("end", "scrub_live", "To live", show=False),
    ]
    CSS = """
    /* Header and Footer self-dock; the timeline takes the remaining space,
       with the inline diff, prompt, and scrub bar flowing beneath it. */
    ActivityStrip { height: 1; padding: 0 1; background: $panel; }
    RunTimeline { height: 1fr; }
    #inline-diff { height: auto; max-height: 40%; border-top: solid $panel; padding: 0 1; }
    PromptInput { height: 3; }
    EvidencePanel { height: auto; }
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
        from intui.console.timeline_widget import RunTimeline

        yield Header()
        yield ActivityStrip(_activity_state, swoosh_glow=6, sweep_seconds=self._sweep_seconds)
        yield RunTimeline(run_timeline_view())
        diff_region = DiffViewer(diff_view(public_safe=self._public_safe), id="inline-diff")
        diff_region.display = False
        yield diff_region
        yield PromptInput(placeholder="type /tasks /files /diff /metrics … or a note")
        yield Static(id="scrub-bar")
        yield Footer()

    def on_mount(self) -> None:
        super().on_mount()
        # Keep the scrub status fresh as events arrive (esp. the total while
        # paused); the held view itself stays frozen via the bridge.
        self.store.subscribe(lambda _snapshot: self._refresh_scrub_bar())
        self._refresh_scrub_bar()

    def action_palette(self) -> None:
        self.open_command_palette(_command_registry())

    # --- Inline diff ---------------------------------------------------------

    def action_toggle_diff(self) -> None:
        """Show/hide the diff inline, in the flow (not a separate view)."""
        region = self.query_one("#inline-diff")
        region.display = not region.display

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
        if intent.name == "toggle_diff":
            self.action_toggle_diff()
            return
        if intent.name == "open_panel":
            self.action_open_panel(str(intent.payload["name"]))
            return
        if intent.name == "open_palette":
            self.open_command_palette(_command_registry())
            return
        if intent.name == "prompt_submitted":
            self._handle_prompt(str(intent.payload.get("text", "")))
            return
        if intent.name in ("copy_path", "open_file", "delete_file"):
            self._handle_file_action(intent)
            return
        self.notify(f"intent: {intent.name}", timeout=2.0)

    def _handle_prompt(self, text: str) -> None:
        """Route a floor-prompt submission.

        ``/name`` runs the matching command (panels, diff, scrub, save);
        anything else is appended to the timeline as a user note.
        """
        if text.startswith("/"):
            word = text[1:].split()[0].lower() if text[1:].strip() else ""
            if word in PANELS:
                self.action_open_panel(word)
            elif word == "diff":
                self.action_toggle_diff()
            elif word == "scrub":
                self.action_scrub_toggle()
            elif word == "save":
                self.action_record()
            else:
                self.notify(f"unknown command: {text}", timeout=3.0)
            return
        self.store.ingest(prompt_message_event(text))

    def action_focus_prompt(self) -> None:
        self.query_one(PromptInput).focus_prompt()

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
    conversation / workspace / metrics / run-status slices reduce the
    canonical stream into the timeline and panels.
    """
    store = Store(
        compose_reducers(
            timeline=timeline_slice(),
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
