"""ProcessMonitorSource: spawn a command and sample its resources as events.

Engine-free (asyncio + stdlib; ``psutil`` is an optional extra imported lazily).
Emits ``process_started`` -> periodic ``metric_sample`` -> ``process_exited`` so
a command's CPU/memory/status reduce through the normal pipeline (replayable,
public-safe) — "run it and watch it work".
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Mapping, Sequence
from datetime import UTC, datetime
from pathlib import PurePath
from time import monotonic
from typing import Any

from intui.events.envelope import Event, Scope


def _load_psutil() -> Any:
    try:
        import psutil  # type: ignore[import-untyped]
    except ImportError as exc:  # pragma: no cover - exercised via monkeypatch
        raise RuntimeError(
            "process metrics need psutil — install the extra: pip install 'in-tui-tion[metrics]'"
        ) from exc
    return psutil


class ProcessMonitorSource:
    """An :class:`EventSource` that spawns ``cmd`` and samples it via ``psutil``.

    Samples every ``interval`` seconds; yields ``process_started`` then a
    ``metric_sample`` per interval then ``process_exited`` (status passed/failed
    from the exit code). No shell; the child's std streams are discarded — this
    watches resources, not output. A vanished process or spawn failure ends the
    stream cleanly.
    """

    def __init__(
        self,
        cmd: Sequence[str],
        *,
        interval: float = 1.0,
        run_id: str = "process",
    ) -> None:
        self._cmd = tuple(cmd)
        self._interval = interval
        self._run_id = run_id
        self._seq = 0

    def _event(
        self, type_: str, *, status: str | None = None, **payload: Any
    ) -> Mapping[str, Any]:
        self._seq += 1
        return Event(
            version="1",
            event_id=f"m{self._seq}",
            run_id=self._run_id,
            timestamp=datetime.now(tz=UTC),
            type=type_,
            scope=Scope(),
            status=status,
            payload=payload,
        ).to_mapping()

    async def __aiter__(self) -> AsyncIterator[Mapping[str, Any]]:
        psutil = _load_psutil()
        label = PurePath(self._cmd[0]).name if self._cmd else "process"
        yield self._event("process_started", label=label)

        process = await asyncio.create_subprocess_exec(
            *self._cmd,
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        start = monotonic()
        try:
            proc = psutil.Process(process.pid)
            proc.cpu_percent()  # prime (first call is a 0.0 baseline)
        except psutil.Error:
            proc = None

        waiter = asyncio.ensure_future(process.wait())
        try:
            while True:
                done, _ = await asyncio.wait({waiter}, timeout=self._interval)
                if waiter in done:
                    break
                sample = _sample(proc, start)
                if sample is not None:
                    yield self._event("metric_sample", **sample)
        finally:
            if not waiter.done():
                await waiter

        exit_code = process.returncode if process.returncode is not None else 0
        yield self._event(
            "process_exited",
            status="passed" if exit_code == 0 else "failed",
            exit_code=exit_code,
            duration_ms=int((monotonic() - start) * 1000),
        )


def _sample(proc: Any, start: float) -> dict[str, Any] | None:
    elapsed_ms = int((monotonic() - start) * 1000)
    if proc is None:
        return {"cpu_percent": 0.0, "rss_bytes": 0, "elapsed_ms": elapsed_ms}
    try:
        cpu = float(proc.cpu_percent())
        rss = int(proc.memory_info().rss)
    except Exception:  # noqa: BLE001 - process may vanish between poll and read
        return None
    return {"cpu_percent": cpu, "rss_bytes": rss, "elapsed_ms": elapsed_ms}
