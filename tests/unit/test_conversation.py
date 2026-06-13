"""Conversation model: reduction + view (engine-free)."""

from datetime import UTC, datetime

from intui.events import Event, Scope
from intui.kit.state import ConversationKind, conversation_slice, conversation_view
from intui.state import Store, compose_reducers


def make_store() -> Store:
    return Store(compose_reducers(conversation=conversation_slice()))


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


def test_message_added_reduces_with_role() -> None:
    store = make_store()
    store.ingest(msg("m1", "message_added", role="agent", text="Hello"))
    entries = store.snapshot.slice("conversation").entries
    assert len(entries) == 1
    assert entries[0].role == "agent"
    assert entries[0].kind is ConversationKind.MESSAGE
    assert entries[0].text == "Hello"


def test_question_and_approval_kinds() -> None:
    store = make_store()
    store.ingest(msg("q1", "question_requested", text="Which target?"))
    store.ingest(msg("a1", "approval_requested", text="Approve plan?"))
    entries = store.snapshot.slice("conversation").entries
    assert entries[0].kind is ConversationKind.QUESTION
    assert entries[1].kind is ConversationKind.APPROVAL
    assert all(e.role == "agent" for e in entries)


def test_order_preserved() -> None:
    store = make_store()
    for i in range(3):
        store.ingest(msg(f"m{i}", "message_added", role="user", text=f"line {i}"))
    entries = store.snapshot.slice("conversation").entries
    assert [e.text for e in entries] == ["line 0", "line 1", "line 2"]
    assert [e.order for e in entries] == [0, 1, 2]


def test_unknown_role_tolerated() -> None:
    store = make_store()
    store.ingest(msg("m1", "message_added", role="robot", text="beep"))
    entry = store.snapshot.slice("conversation").entries[0]
    assert entry.role == "robot"  # preserved, not dropped


def test_unknown_event_passes_through() -> None:
    store = make_store()
    before = store.snapshot.slice("conversation")
    store.ingest(msg("x", "unrelated"))
    assert store.snapshot.slice("conversation") == before


def test_conversation_view_tags() -> None:
    store = make_store()
    store.ingest(msg("m1", "message_added", role="agent", text="hi"))
    store.ingest(msg("q1", "question_requested", text="why?"))
    rows = conversation_view()(store.snapshot).entries
    tags = [r.tag for r in rows]
    # tags carry kind/role textually (non-color)
    assert any("agent" in t for t in tags)
    assert any("question" in t for t in tags)


def test_conversation_view_memoized() -> None:
    store = make_store()
    view = conversation_view()
    assert view(store.snapshot) is view(store.snapshot)


def test_empty_conversation_view() -> None:
    assert conversation_view()(make_store().snapshot).entries == ()


def test_prompt_message_event_builds_user_message() -> None:
    from intui.kit.state import ConversationKind, prompt_message_event

    store = make_store()
    store.ingest(prompt_message_event("build me a service"))
    entry = store.snapshot.slice("conversation").entries[0]
    assert entry.role == "user"
    assert entry.kind is ConversationKind.MESSAGE
    assert entry.text == "build me a service"


def test_prompt_message_event_unique_ids() -> None:
    from intui.kit.state import prompt_message_event

    a = prompt_message_event("one")
    b = prompt_message_event("two")
    assert a.event_id != b.event_id  # distinct so the stream does not dedupe
