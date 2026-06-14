"""Conversation model: a role/kind-tagged transcript reduced from events.

Engine-free. ``message_added`` (with a role), ``question_requested``, and
``approval_requested`` reduce into an ordered, append-only transcript;
unknown roles are preserved, not dropped.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from intui.events.envelope import Event, Scope
from intui.state.snapshot import Snapshot
from intui.viewmodels.selector import Selector

_KNOWN_ROLES = {"agent", "user", "system"}
_prompt_counter = itertools.count()

#: Canonical event types the conversation reducer consumes (stream contract).
CONVERSATION_EVENT_TYPES = frozenset({"message_added", "question_requested", "approval_requested"})


class ConversationKind(Enum):
    MESSAGE = "message"
    QUESTION = "question"
    APPROVAL = "approval"


@dataclass(frozen=True, slots=True)
class ConversationEntry:
    order: int
    role: str
    kind: ConversationKind
    text: str


@dataclass(frozen=True, slots=True)
class ConversationState:
    entries: tuple[ConversationEntry, ...] = ()


@dataclass(frozen=True, slots=True)
class ConversationRow:
    order: int
    role: str
    kind: ConversationKind
    text: str
    tag: str


@dataclass(frozen=True, slots=True)
class ConversationView:
    entries: tuple[ConversationRow, ...] = ()


def conversation_slice() -> tuple[Any, ConversationState]:
    """``(reducer, initial)`` for ``compose_reducers(conversation=...)``."""

    def reduce(state: ConversationState, event: Event) -> ConversationState:
        entry = _entry_for(event, len(state.entries))
        if entry is None:
            return state
        return replace(state, entries=(*state.entries, entry))

    return reduce, ConversationState()


def _entry_for(event: Event, order: int) -> ConversationEntry | None:
    if event.type == "message_added":
        role = event.payload.get("role")
        return ConversationEntry(
            order=order,
            role=role if isinstance(role, str) and role else "unknown",
            kind=ConversationKind.MESSAGE,
            text=_text(event),
        )
    if event.type == "question_requested":
        return ConversationEntry(order, "agent", ConversationKind.QUESTION, _text(event))
    if event.type == "approval_requested":
        return ConversationEntry(order, "agent", ConversationKind.APPROVAL, _text(event))
    return None


def _text(event: Event) -> str:
    text = event.payload.get("text")
    if isinstance(text, str):
        return text
    return event.summary or ""


_ROLE_TAGS = {"agent": "agent", "user": "you", "system": "system"}


def conversation_view(slice_name: str = "conversation") -> Selector[ConversationView]:
    def project(snapshot: Snapshot) -> ConversationView:
        state: ConversationState = snapshot.slice(slice_name)
        return ConversationView(entries=tuple(_row(e) for e in state.entries))

    return Selector(project)


def prompt_message_event(text: str, run_id: str = "", event_id: str | None = None) -> Event:
    """Build the ``message_added`` (role=user) event for a submitted prompt.

    Lets an application append a prompt submission to the conversation in one
    call. Event ids are unique by default so the stream does not dedupe them.
    """
    if event_id is None:
        event_id = f"prompt-{next(_prompt_counter)}-{datetime.now(tz=UTC).timestamp()}"
    return Event(
        version="1",
        event_id=event_id,
        run_id=run_id,
        timestamp=datetime.now(tz=UTC),
        type="message_added",
        scope=Scope(),
        payload={"role": "user", "text": text},
    )


def _row(entry: ConversationEntry) -> ConversationRow:
    if entry.kind is ConversationKind.QUESTION:
        tag = "? question"
    elif entry.kind is ConversationKind.APPROVAL:
        tag = "approval"
    else:
        tag = _ROLE_TAGS.get(entry.role, f"({entry.role})")
    return ConversationRow(
        order=entry.order, role=entry.role, kind=entry.kind, text=entry.text, tag=tag
    )
