"""hello_replay: a state-driven TUI fed by a scripted event stream.

Foundation-story scope: a scripted MemorySource paced for visibility, a
status line and scrolling item list bound to view models, and stream-health
display. Later stories switch this to a recorded .jsonl file and add intents,
themes, and the Signal primitive.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Mapping
from datetime import UTC, datetime, timedelta
from typing import Any

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Footer, Header

from intui.app import IntuiApp
from intui.events import Event, MemorySource, Scope, StreamState
from intui.state import Snapshot, Store, compose_reducers
from intui.viewmodels import health_view, selector
from intui.widgets import BoundWidget

# --- A simulated multi-step run, expressed as events ----------------------

_T0 = datetime(2026, 6, 12, 12, 0, 0, tzinfo=UTC)

_SCRIPT: list[tuple[str, str, dict[str, Any]]] = [
    ("run_started", "running", {"goal": "Assemble the demo application"}),
    ("task_started", "running", {"name": "Parse the blueprint"}),
    ("task_completed", "passed", {"name": "Parse the blueprint"}),
    ("task_started", "running", {"name": "Generate the scaffold"}),
    ("task_completed", "passed", {"name": "Generate the scaffold"}),
    ("task_started", "running", {"name": "Wire the event pipeline"}),
    ("task_completed", "passed", {"name": "Wire the event pipeline"}),
    ("gate_started", "verifying", {"name": "Run verification suite"}),
    ("gate_passed", "passed", {"name": "Run verification suite"}),
    ("run_completed", "passed", {"summary": "All gates green"}),
]


def scripted_events() -> list[Event]:
    return [
        Event(
            version="1",
            event_id=f"evt-{i:03d}",
            run_id="run-demo",
            timestamp=_T0 + timedelta(seconds=i),
            type=type_,
            scope=Scope(session_id="session-demo"),
            status=status,
            summary=str(payload.get("name") or payload.get("goal") or payload.get("summary")),
            payload=payload,
        )
        for i, (type_, status, payload) in enumerate(_SCRIPT)
    ]


class PacedSource:
    """Wrap a source to deliver events at a human-watchable pace."""

    def __init__(self, events: list[Event], events_per_second: float = 2.0) -> None:
        self._inner = MemorySource(events)
        self._delay = 1.0 / events_per_second

    async def __aiter__(self) -> AsyncIterator[Mapping[str, Any]]:
        import asyncio

        async for raw in self._inner:
            yield raw
            await asyncio.sleep(self._delay)


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


def build_app() -> HelloReplayApp:
    store = Store(compose_reducers(log=(log_reducer, ()), status=(status_reducer, "idle")))
    return HelloReplayApp(store=store, source=PacedSource(scripted_events()))


if __name__ == "__main__":
    build_app().run()
