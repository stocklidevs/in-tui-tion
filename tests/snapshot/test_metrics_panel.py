"""MetricsPanel widget: renders status/usage/sparkline (Pilot)."""

from __future__ import annotations

from datetime import UTC, datetime

from textual.app import App, ComposeResult

from intui.events import Event, Scope
from intui.kit import MetricsPanel
from intui.kit.state import metrics_slice, metrics_view
from intui.state import Store, compose_reducers
from intui.widgets.bridge import StoreBridge

_seq = 0


def _event(type_: str, *, status: str | None = None, **payload: object) -> Event:
    global _seq
    _seq += 1
    return Event(
        version="1",
        event_id=f"e{_seq}",
        run_id="r1",
        timestamp=datetime(2026, 6, 14, tzinfo=UTC),
        type=type_,
        scope=Scope(),
        status=status,
        payload=payload,
    )


class _Harness(App[None]):
    def __init__(self, store: Store) -> None:
        super().__init__()
        self.store = store
        self.bridge = StoreBridge(store, self)

    def compose(self) -> ComposeResult:
        yield MetricsPanel(metrics_view())


def _store() -> Store:
    store = Store(compose_reducers(metrics=metrics_slice()))
    store.ingest(_event("process_started", label="build.py"))
    store.ingest(_event("metric_sample", cpu_percent=40.0, rss_bytes=53_400_000, elapsed_ms=1200))
    store.ingest(_event("metric_sample", cpu_percent=12.0, rss_bytes=20_000_000, elapsed_ms=1700))
    return store


async def test_metrics_panel_shows_usage() -> None:
    app = _Harness(_store())
    async with app.run_test(size=(80, 24)) as pilot:
        await pilot.pause()
        text = app.query_one(MetricsPanel).summary_text()
        assert "build.py" in text
        assert "MB" in text  # human memory
        assert "%" in text  # cpu


async def test_metrics_panel_empty_state() -> None:
    store = Store(compose_reducers(metrics=metrics_slice()))
    app = _Harness(store)
    async with app.run_test(size=(80, 24)) as pilot:
        await pilot.pause()
        assert app.query_one(MetricsPanel).summary_text() != ""  # shows an empty state


async def test_metrics_panel_reflects_exit() -> None:
    store = _store()
    app = _Harness(store)
    async with app.run_test(size=(80, 24)) as pilot:
        await pilot.pause()
        store.ingest(_event("process_exited", status="passed", exit_code=0, duration_ms=1800))
        await pilot.pause()
        assert app.query_one(MetricsPanel).status() == "passed"
