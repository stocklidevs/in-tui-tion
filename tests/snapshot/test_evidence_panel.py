"""US2: the evidence panel — labeled rows, lists, status, n/a, update, redaction."""

from datetime import UTC, datetime
from typing import Any

from textual.app import ComposeResult

from intui.app import IntuiApp
from intui.events import Event, Scope
from intui.kit import EvidencePanel
from intui.kit.state import artifacts_slice, evidence_view
from intui.state import Store, compose_reducers


def evidence_event(eid: str = "e1", **over: object) -> Event:
    payload: dict[str, Any] = {
        "title": "Evidence",
        "metrics": [
            {"key": "pass_rate", "label": "Pass rate", "value": "92%", "status": "passed"},
            {"key": "failures", "label": "Failures", "value": ["timeout", "drift"]},
            {"key": "workdir", "label": "Workdir", "value": "C:\\Users\\op\\run", "unsafe": True},
        ],
    }
    payload.update(over)
    return Event(
        version="1",
        event_id=eid,
        run_id="r1",
        timestamp=datetime(2026, 6, 13, tzinfo=UTC),
        type="evidence_ready",
        scope=Scope(),
        payload=payload,
    )


class EvidenceApp(IntuiApp):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.panel = EvidencePanel(evidence_view())

    def compose(self) -> ComposeResult:
        yield self.panel


def build() -> tuple[EvidenceApp, Store]:
    store = Store(compose_reducers(artifacts=artifacts_slice()))
    return EvidenceApp(store=store), store


async def test_labeled_metric_rows() -> None:
    app, store = build()
    async with app.run_test() as pilot:
        await pilot.pause()
        store.ingest(evidence_event())
        await pilot.pause(0.05)
        text = app.panel.panel_text()
        assert "Pass rate" in text and "92%" in text


async def test_list_metric_enumerated() -> None:
    app, store = build()
    async with app.run_test() as pilot:
        await pilot.pause()
        store.ingest(evidence_event())
        await pilot.pause(0.05)
        text = app.panel.panel_text()
        assert "timeout" in text and "drift" in text


async def test_status_metric_has_glyph_and_label() -> None:
    app, store = build()
    async with app.run_test() as pilot:
        await pilot.pause()
        store.ingest(evidence_event())
        await pilot.pause(0.05)
        row = app.panel.row_text("pass_rate")
        # status conveyed by a label/glyph, not color alone
        assert "passed" in row.lower() or "✔" in row


async def test_unsafe_value_redacted_by_default() -> None:
    app, store = build()
    async with app.run_test() as pilot:
        await pilot.pause()
        store.ingest(evidence_event())
        await pilot.pause(0.05)
        row = app.panel.row_text("workdir")
        assert "C:\\Users\\op\\run" not in row
        assert "Workdir" in row  # label preserved


async def test_latest_evidence_updates_panel() -> None:
    app, store = build()
    async with app.run_test() as pilot:
        await pilot.pause()
        store.ingest(evidence_event())
        await pilot.pause(0.05)
        store.ingest(
            evidence_event(
                eid="e2",
                metrics=[{"key": "pass_rate", "label": "Pass rate", "value": "100%"}],
            )
        )
        await pilot.pause(0.05)
        assert "100%" in app.panel.panel_text()


async def test_empty_state() -> None:
    app, _ = build()
    async with app.run_test() as pilot:
        await pilot.pause()
        assert "no evidence" in app.panel.panel_text().lower()
