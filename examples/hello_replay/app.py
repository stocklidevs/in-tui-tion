"""hello_replay: a state-driven TUI replaying a recorded event stream.

The bundled ``recording.jsonl`` is a simulated multi-step run; the app
replays it at a human-watchable pace and renders a status line, a scrolling
event log, and stream health — all derived from events through the pipeline.
Later stories add intents, theme switching, and the Signal primitive.
"""

from __future__ import annotations

from pathlib import Path

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Footer, Header

from intui.app import IntuiApp
from intui.events import Event, JsonlReplaySource, StreamState
from intui.state import Snapshot, Store, compose_reducers
from intui.viewmodels import health_view, selector
from intui.widgets import BoundWidget

RECORDING = Path(__file__).parent / "recording.jsonl"


# --- Reducers: fold run events into application state ----------------------


def log_reducer(lines: tuple[str, ...], event: Event) -> tuple[str, ...]:
    if event.type in {
        "run_started",
        "task_started",
        "task_completed",
        "gate_started",
        "gate_passed",
        "run_completed",
    }:
        marker = {"running": "...", "verifying": ">>>", "passed": " ok"}.get(
            event.status or "", "  ?"
        )
        return (*lines, f"[{marker}] {event.type:<14} {event.summary}")
    return lines


def status_reducer(status: str, event: Event) -> str:
    return event.status or status


# --- View models ------------------------------------------------------------


@selector
def log_vm(snapshot: Snapshot) -> tuple[str, ...]:
    return snapshot.slice("log")


@selector
def status_vm(snapshot: Snapshot) -> str:
    health = health_view(snapshot)
    status = snapshot.slice("status")
    if health.state is not StreamState.LIVE:
        return f"run status: {status}  |  stream: {health.label}"
    return f"run status: {status}"


# --- Widgets ----------------------------------------------------------------


class StatusLine(BoundWidget):
    def render_view(self, vm: str) -> str:
        return vm


class EventLog(BoundWidget):
    def render_view(self, vm: tuple[str, ...]) -> str:
        return "\n".join(vm) if vm else "waiting for events..."


# --- The application --------------------------------------------------------


class HelloReplayApp(IntuiApp):
    TITLE = "in-TUI-tion · hello_replay"
    BINDINGS = [("q", "quit", "Quit")]
    CSS = """
    StatusLine { dock: top; height: 1; padding: 0 1; background: $panel; }
    VerticalScroll { padding: 0 1; }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        yield StatusLine(status_vm)
        yield VerticalScroll(EventLog(log_vm))
        yield Footer()


def build_app(events_per_second: float = 2.0) -> HelloReplayApp:
    store = Store(compose_reducers(log=(log_reducer, ()), status=(status_reducer, "idle")))
    return HelloReplayApp(store=store, source=JsonlReplaySource(RECORDING, rate=events_per_second))


if __name__ == "__main__":
    build_app().run()
