"""Confirmation flow: risky intents are held until explicitly confirmed (FR-016)."""

from intui.actions import ConfirmationFlow, Intent


def make_flow() -> tuple[ConfirmationFlow, list[Intent]]:
    delivered: list[Intent] = []
    flow = ConfirmationFlow(deliver=delivered.append)
    return flow, delivered


def test_non_risky_intent_bypasses_confirmation() -> None:
    flow, delivered = make_flow()
    flow.submit(Intent(name="toggle"))
    assert delivered == [Intent(name="toggle")]
    assert flow.pending is None


def test_risky_intent_is_held_until_confirmed() -> None:
    flow, delivered = make_flow()
    risky = Intent(name="clear_history", risky=True)
    flow.submit(risky)
    assert delivered == []  # held, not delivered
    assert flow.pending == risky
    flow.confirm()
    assert delivered == [risky]
    assert flow.pending is None


def test_cancelled_intent_is_never_delivered() -> None:
    flow, delivered = make_flow()
    flow.submit(Intent(name="clear_history", risky=True))
    flow.cancel()
    assert delivered == []
    assert flow.pending is None


def test_confirm_without_pending_is_a_noop() -> None:
    flow, delivered = make_flow()
    flow.confirm()
    flow.cancel()
    assert delivered == []


def test_new_risky_intent_replaces_nothing_while_pending() -> None:
    # Submitting while a confirmation is pending is rejected (the prompt owns
    # the interaction until resolved) - the second intent is not delivered.
    flow, delivered = make_flow()
    first = Intent(name="clear_history", risky=True)
    flow.submit(first)
    accepted = flow.submit(Intent(name="other", risky=True))
    assert accepted is False
    assert flow.pending == first
    flow.confirm()
    assert delivered == [first]


def test_non_risky_during_pending_is_also_held_off() -> None:
    flow, delivered = make_flow()
    flow.submit(Intent(name="clear_history", risky=True))
    accepted = flow.submit(Intent(name="toggle"))
    assert accepted is False
    assert delivered == []
