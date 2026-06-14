"""Metrics slice + metrics_view + sparkline/human_bytes (engine-free)."""

from __future__ import annotations

from datetime import UTC, datetime

from intui.events import Event, Scope
from intui.kit.state import (
    KNOWN_EVENT_TYPES,
    METRICS_EVENT_TYPES,
    human_bytes,
    metrics_slice,
    metrics_view,
    sparkline,
)
from intui.state import Store, compose_reducers

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


def _store(window: int = 60) -> Store:
    return Store(compose_reducers(metrics=metrics_slice(window)))


def test_started_sets_running_and_label() -> None:
    store = _store()
    store.ingest(_event("process_started", label="build.py"))
    m = store.snapshot.slice("metrics")
    assert m.status == "running" and m.label == "build.py"


def test_sample_updates_latest_and_peak() -> None:
    store = _store()
    store.ingest(_event("process_started", label="x"))
    store.ingest(_event("metric_sample", cpu_percent=10.0, rss_bytes=100, elapsed_ms=500))
    store.ingest(_event("metric_sample", cpu_percent=20.0, rss_bytes=50, elapsed_ms=1000))
    m = store.snapshot.slice("metrics")
    assert m.cpu_percent == 20.0 and m.rss_bytes == 50
    assert m.peak_rss_bytes == 100  # peak retained
    assert m.elapsed_ms == 1000
    assert len(m.samples) == 2


def test_history_is_bounded() -> None:
    store = _store(window=3)
    for i in range(5):
        store.ingest(_event("metric_sample", cpu_percent=float(i), rss_bytes=i, elapsed_ms=i))
    m = store.snapshot.slice("metrics")
    assert len(m.samples) == 3
    assert [s.cpu_percent for s in m.samples] == [2.0, 3.0, 4.0]  # last 3


def test_exit_status_passed_and_failed() -> None:
    store = _store()
    store.ingest(_event("process_started", label="x"))
    store.ingest(_event("process_exited", status="passed", exit_code=0, duration_ms=1500))
    m = store.snapshot.slice("metrics")
    assert m.status == "passed" and m.exit_code == 0 and m.elapsed_ms == 1500

    store2 = _store()
    store2.ingest(_event("process_exited", status="failed", exit_code=1, duration_ms=10))
    assert store2.snapshot.slice("metrics").status == "failed"


def test_metrics_view_human_and_sparklines() -> None:
    store = _store()
    store.ingest(_event("process_started", label="build.py"))
    store.ingest(_event("metric_sample", cpu_percent=40.0, rss_bytes=53_400_000, elapsed_ms=1200))
    store.ingest(_event("metric_sample", cpu_percent=10.0, rss_bytes=10_000_000, elapsed_ms=1700))
    vm = metrics_view()(store.snapshot)
    assert vm.present and vm.label == "build.py"
    assert vm.glyph and vm.status_label
    assert "MB" in vm.rss_human and "MB" in vm.peak_human
    assert vm.cpu_spark and vm.mem_spark
    assert vm.sample_count == 2


def test_metrics_view_redacts_label_by_default() -> None:
    store = _store()
    store.ingest(_event("process_started", label="/home/alice/secret/build.py"))
    safe = metrics_view()(store.snapshot)
    assert "alice" not in safe.label
    raw = metrics_view(public_safe=False)(store.snapshot)
    assert "alice" in raw.label


def test_metrics_view_empty_state() -> None:
    assert metrics_view()(_store().snapshot).present is False


def test_sparkline_helper() -> None:
    assert sparkline([]) == ""
    line = sparkline([0, 5, 10])
    assert len(line) == 3 and line[0] != line[-1]  # rises


def test_human_bytes_helper() -> None:
    assert human_bytes(0) == "0 B"
    assert human_bytes(1536).endswith("KB")
    assert "MB" in human_bytes(53_400_000)


def test_event_types_in_vocabulary() -> None:
    assert METRICS_EVENT_TYPES <= KNOWN_EVENT_TYPES
