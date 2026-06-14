"""Producer SDK: emit canonical events in a few lines (engine-free).

``run_recorder(...)`` returns a :class:`RunRecorder` that produces **bare,
valid canonical envelopes** (the stream contract) to a file, stdout, or a
callable — so any tool becomes ``intui watch``-able with no JSON by hand and no
adapter. Reuses :class:`~intui.events.Event`/:class:`~intui.events.Scope` for
construction and ``to_mapping()`` for serialization (one source of truth).

Engine-free (stdlib + ``intui.events``); re-exported from the ``intui`` root.
"""

from __future__ import annotations

import difflib
import json
import sys
import uuid
from collections.abc import Callable, Mapping
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from types import TracebackType
from typing import Any, TextIO

from intui.events.envelope import Event, Scope

Sink = Callable[[Mapping[str, Any]], None]
Clock = Callable[[], datetime]


# ASCII-safe JSON (the json default): non-ASCII becomes \uXXXX, so a line is
# portable across any stdout/pipe encoding (e.g. a Windows cp1252 pipe) and any
# reader decodes it back. Avoids mojibake when a consumer spawns the producer.
def _dumps(envelope: Mapping[str, Any]) -> str:
    return json.dumps(envelope) + "\n"


def _stdout_sink(envelope: Mapping[str, Any]) -> None:
    sys.stdout.write(_dumps(envelope))
    sys.stdout.flush()


def _file_sink(handle: TextIO) -> Sink:
    def sink(envelope: Mapping[str, Any]) -> None:
        handle.write(_dumps(envelope))
        handle.flush()

    return sink


def run_recorder(
    sink: Path | str | TextIO | Sink | None = None,
    *,
    run_id: str | None = None,
    clock: Clock | None = None,
) -> RunRecorder:
    """Create a :class:`RunRecorder`.

    ``sink``: a file path (opened, closed on recorder close), a text file
    object, a callable taking each envelope mapping, or ``None`` for stdout.
    ``run_id`` defaults to a generated id; ``clock`` defaults to ``now(UTC)``.
    """
    owns_file = False
    resolved: Sink
    if sink is None:
        resolved = _stdout_sink
    elif isinstance(sink, (str, Path)):
        # Long-lived handle owned by the recorder (closed in close()); not a
        # with-block here by design.
        handle = Path(sink).open("w", encoding="utf-8", newline="\n")  # noqa: SIM115
        resolved = _file_sink(handle)
        owns_file = True
    elif callable(sink):
        resolved = sink
    else:  # a text file object
        resolved = _file_sink(sink)
    return RunRecorder(
        resolved,
        run_id=run_id or f"run-{uuid.uuid4().hex[:8]}",
        clock=clock or (lambda: datetime.now(tz=UTC)),
        _file=handle if owns_file else None,
    )


class RunRecorder:
    """Emits canonical envelopes. Build via :func:`run_recorder`."""

    def __init__(
        self,
        sink: Sink,
        *,
        run_id: str,
        clock: Clock,
        _file: TextIO | None = None,
    ) -> None:
        self.run_id = run_id
        self._sink = sink
        self._clock = clock
        self._file = _file
        self._seq = 0
        self._closed = False

    # --- core ----------------------------------------------------------------

    def emit(
        self,
        type: str,
        *,
        task_id: str | None = None,
        work_item_id: str | None = None,
        lane_id: str | None = None,
        session_id: str | None = None,
        status: str | None = None,
        summary: str | None = None,
        **payload: Any,
    ) -> Event:
        """Emit a canonical event of any ``type`` (the generic escape hatch)."""
        if self._closed:
            raise RuntimeError("recorder is closed")
        self._seq += 1
        event = Event(
            version="1",
            event_id=f"e{self._seq}",
            run_id=self.run_id,
            timestamp=self._clock(),
            type=type,
            scope=Scope(
                session_id=session_id,
                task_id=task_id,
                work_item_id=work_item_id,
                lane_id=lane_id,
            ),
            status=status,
            summary=summary,
            payload=payload,
        )
        self._sink(event.to_mapping())
        return event

    # --- tasks & work items --------------------------------------------------

    def task_created(
        self, task_id: str, title: str | None = None, *, summary: str | None = None
    ) -> Event:
        return self.emit("task_created", task_id=task_id, summary=summary, **_name(title))

    def task_started(
        self, task_id: str, title: str | None = None, *, summary: str | None = None
    ) -> Event:
        return self.emit("task_started", task_id=task_id, summary=summary, **_name(title))

    def task_blocked(
        self, task_id: str, title: str | None = None, *, summary: str | None = None
    ) -> Event:
        return self.emit("task_blocked", task_id=task_id, summary=summary, **_name(title))

    def task_completed(
        self, task_id: str, *, status: str = "passed", summary: str | None = None
    ) -> Event:
        return self.emit("task_completed", task_id=task_id, status=status, summary=summary)

    def work_item_started(
        self, work_item_id: str, *, task_id: str | None = None, title: str | None = None
    ) -> Event:
        return self.emit(
            "work_item_started", task_id=task_id, work_item_id=work_item_id, **_name(title)
        )

    def work_item_completed(
        self, work_item_id: str, *, task_id: str | None = None, status: str = "passed"
    ) -> Event:
        return self.emit(
            "work_item_completed", task_id=task_id, work_item_id=work_item_id, status=status
        )

    # --- lanes / subagents ---------------------------------------------------

    def subagent_started(
        self, lane_id: str, *, name: str | None = None, task_id: str | None = None
    ) -> Event:
        return self.emit("subagent_started", lane_id=lane_id, task_id=task_id, **_name(name))

    def subagent_activity(self, lane_id: str, *, summary: str) -> Event:
        return self.emit("subagent_activity", lane_id=lane_id, summary=summary)

    def subagent_completed(self, lane_id: str, *, status: str = "passed") -> Event:
        return self.emit("subagent_completed", lane_id=lane_id, status=status)

    # --- conversation --------------------------------------------------------

    def message(self, role: str, text: str) -> Event:
        return self.emit("message_added", role=role, text=text)

    def agent(self, text: str) -> Event:
        return self.message("agent", text)

    def user(self, text: str) -> Event:
        return self.message("user", text)

    def system(self, text: str) -> Event:
        return self.message("system", text)

    def question(self, text: str) -> Event:
        return self.emit("question_requested", text=text)

    def approval(self, text: str) -> Event:
        return self.emit("approval_requested", text=text)

    # --- artifacts -----------------------------------------------------------

    def diff(self, path: str, *, before: str, after: str, public_safe: bool = True) -> Event:
        """Emit ``diff_ready`` for one file, building a unified diff via difflib."""
        unified = "".join(
            difflib.unified_diff(
                before.splitlines(keepends=True),
                after.splitlines(keepends=True),
                fromfile=f"a/{path}",
                tofile=f"b/{path}",
            )
        )
        return self.diff_unified(unified, title=path, public_safe=public_safe)

    def diff_unified(
        self, unified: str, *, title: str = "diff", public_safe: bool = True
    ) -> Event:
        return self.emit("diff_ready", unified=unified, title=title, public_safe=public_safe)

    def evidence(
        self,
        *,
        title: str = "evidence",
        public_safe: bool = True,
        **metrics: Any,
    ) -> Event:
        rows = [
            {"key": key, "label": key.replace("_", " "), "value": value}
            for key, value in metrics.items()
        ]
        return self.emit("evidence_ready", title=title, metrics=rows, public_safe=public_safe)

    # --- views / modes / activity / run lifecycle ----------------------------

    def view(self, view: str) -> Event:
        return self.emit("view_selected", view=view)

    def mode(self, mode: str) -> Event:
        return self.emit("mode_changed", mode=mode)

    def activity(self, state: str) -> Event:
        return self.emit("activity_set", state=state)

    def run_started(self, *, summary: str | None = None) -> Event:
        return self.emit("run_started", summary=summary)

    def run_completed(self, *, status: str = "passed", summary: str | None = None) -> Event:
        return self.emit("run_completed", status=status, summary=summary)

    def run_failed(self, *, summary: str | None = None) -> Event:
        return self.emit("run_failed", status="failed", summary=summary)

    # --- ergonomic context managers ------------------------------------------

    @contextmanager
    def run(self, *, summary: str | None = None) -> Any:
        """Bracket a block with ``run_started`` / ``run_completed`` (``run_failed``
        if it raises)."""
        self.run_started(summary=summary)
        try:
            yield self
        except BaseException:
            self.run_failed()
            raise
        else:
            self.run_completed()

    def task(self, task_id: str, title: str | None = None) -> Task:
        """A task handle/context manager: ``task_started`` on enter,
        ``task_completed`` on exit (``status: failed`` if the block raises)."""
        return Task(self, task_id, title)

    # --- lifecycle -----------------------------------------------------------

    def close(self) -> None:
        if self._file is not None and not self._closed:
            self._file.close()
        self._closed = True

    def __enter__(self) -> RunRecorder:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.close()


class Task:
    """A task scope: emits ``task_started``/``task_completed`` and spawns
    work items scoped to it."""

    def __init__(self, recorder: RunRecorder, task_id: str, title: str | None) -> None:
        self._rec = recorder
        self.task_id = task_id
        self._title = title

    def work_item(self, work_item_id: str, title: str | None = None) -> WorkItem:
        return WorkItem(self._rec, self.task_id, work_item_id, title)

    def note(self, text: str) -> Event:
        return self._rec.emit("message_added", role="agent", text=text, task_id=self.task_id)

    def __enter__(self) -> Task:
        self._rec.task_started(self.task_id, self._title)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self._rec.task_completed(
            self.task_id, status="failed" if exc_type is not None else "passed"
        )


class WorkItem:
    """A work-item scope under a task: emits the started/completed pair."""

    def __init__(
        self, recorder: RunRecorder, task_id: str, work_item_id: str, title: str | None
    ) -> None:
        self._rec = recorder
        self._task_id = task_id
        self.work_item_id = work_item_id
        self._title = title

    def __enter__(self) -> WorkItem:
        self._rec.work_item_started(self.work_item_id, task_id=self._task_id, title=self._title)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self._rec.work_item_completed(
            self.work_item_id,
            task_id=self._task_id,
            status="failed" if exc_type is not None else "passed",
        )


def _name(title: str | None) -> dict[str, str]:
    return {"name": title} if title else {}
