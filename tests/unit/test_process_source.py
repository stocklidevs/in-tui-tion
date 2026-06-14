"""ProcessMonitorSource: spawn + sample a command into metric events."""

from __future__ import annotations

import asyncio
import sys

import pytest

from intui.events import ProcessMonitorSource
from intui.events.stream import StreamState
from intui.kit.state import metrics_slice
from intui.state import Store, compose_reducers


def _run(cmd: list[str], **kw: object) -> Store:
    store = Store(compose_reducers(metrics=metrics_slice()))
    source = ProcessMonitorSource(cmd, interval=0.05, **kw)  # type: ignore[arg-type]
    asyncio.run(store.run(source))
    return store


def test_monitor_short_command_passes() -> None:
    store = _run([sys.executable, "-c", "import time; time.sleep(0.25)"])
    m = store.snapshot.slice("metrics")
    assert m.status == "passed"
    assert store.snapshot.health.state == StreamState.ENDED


def test_monitor_nonzero_exit_fails() -> None:
    store = _run([sys.executable, "-c", "import sys; sys.exit(3)"])
    m = store.snapshot.slice("metrics")
    assert m.status == "failed" and m.exit_code == 3


def test_monitor_emits_label() -> None:
    store = _run([sys.executable, "-c", "pass"])
    # label is the basename of argv[0] (the interpreter), sanitized
    assert store.snapshot.slice("metrics").label


def test_missing_psutil_raises_clear_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(sys.modules, "psutil", None)  # force ImportError on import
    source = ProcessMonitorSource([sys.executable, "-c", "pass"], interval=0.05)

    async def drive() -> None:
        async for _ in source:
            pass

    with pytest.raises(RuntimeError, match=r"in-tui-tion\[metrics\]"):
        asyncio.run(drive())
