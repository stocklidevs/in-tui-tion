"""Intent semantics: immutable, named, delivered to the app's handler (FR-014)."""

import dataclasses

import pytest

from intui.actions import Intent


def test_intent_carries_name_payload_risky() -> None:
    intent = Intent(name="approve", payload={"task_id": "t1"}, risky=True)
    assert intent.name == "approve"
    assert intent.payload == {"task_id": "t1"}
    assert intent.risky is True


def test_intent_defaults() -> None:
    intent = Intent(name="toggle")
    assert intent.payload == {}
    assert intent.risky is False


def test_intent_is_frozen() -> None:
    intent = Intent(name="approve")
    with pytest.raises(dataclasses.FrozenInstanceError):
        intent.name = "reject"  # type: ignore[misc]


def test_intent_value_equality() -> None:
    assert Intent(name="a", payload={"k": 1}) == Intent(name="a", payload={"k": 1})
    assert Intent(name="a") != Intent(name="b")


async def test_handler_protocol_receives_intent() -> None:
    received: list[Intent] = []

    async def handler(intent: Intent) -> None:
        received.append(intent)

    intent = Intent(name="retry", payload={"run": "r1"})
    await handler(intent)
    assert received == [intent]
