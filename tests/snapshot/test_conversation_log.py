"""US2: the conversation log — order, role/kind tags, empty state."""

from datetime import UTC, datetime
from typing import Any

from textual.app import ComposeResult

from intui.app import IntuiApp
from intui.events import Event, Scope
from intui.kit import ConversationLog
from intui.kit.state import conversation_slice, conversation_view
from intui.state import Store, compose_reducers


def msg(eid: str, type_: str, **payload: object) -> Event:
    return Event(
        version="1",
        event_id=eid,
        run_id="r1",
        timestamp=datetime(2026, 6, 13, tzinfo=UTC),
        type=type_,
        scope=Scope(),
        payload=payload,
    )


class ConvApp(IntuiApp):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.conv_log = ConversationLog(conversation_view())

    def compose(self) -> ComposeResult:
        yield self.conv_log


def build() -> tuple[ConvApp, Store]:
    store = Store(compose_reducers(conversation=conversation_slice()))
    return ConvApp(store=store), store


async def test_renders_transcript_in_order_with_tags() -> None:
    app, store = build()
    async with app.run_test() as pilot:
        await pilot.pause()
        store.ingest(msg("m1", "message_added", role="agent", text="Planning the run"))
        store.ingest(msg("u1", "message_added", role="user", text="Go ahead"))
        store.ingest(msg("q1", "question_requested", text="Which environment?"))
        await pilot.pause(0.05)
        text = app.conv_log.log_text()
        assert "Planning the run" in text
        assert "Go ahead" in text
        assert "Which environment?" in text
        # order preserved
        assert text.index("Planning the run") < text.index("Go ahead") < text.index("Which environment?")


async def test_role_and_kind_identifiable_without_color() -> None:
    app, store = build()
    async with app.run_test() as pilot:
        await pilot.pause()
        store.ingest(msg("m1", "message_added", role="agent", text="hi"))
        store.ingest(msg("q1", "question_requested", text="why?"))
        await pilot.pause(0.05)
        text = app.conv_log.log_text()
        assert "agent" in text
        assert "question" in text  # question kind visible in the tag


async def test_empty_state() -> None:
    app, _ = build()
    async with app.run_test() as pilot:
        await pilot.pause()
        assert "no messages" in app.conv_log.log_text().lower()
