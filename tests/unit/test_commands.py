"""Command model: registry, availability, matcher, and command_view selector."""

from datetime import UTC, datetime

import pytest

from intui.actions import Intent
from intui.events import Event, Scope
from intui.kit.state import (
    Command,
    CommandRegistry,
    command_view,
    filter_commands,
    match_score,
)
from intui.state import Store, compose_reducers

# --- Registry & availability -------------------------------------------------


def flag_reducer(flag: bool, event: Event) -> bool:
    if event.type == "enable":
        return True
    if event.type == "disable":
        return False
    return flag


def make_store() -> Store:
    return Store(compose_reducers(ready=(flag_reducer, False)))


def event(type_: str) -> Event:
    return Event(
        version="1",
        event_id=f"e-{type_}-{datetime.now(tz=UTC).timestamp()}",
        run_id="r1",
        timestamp=datetime(2026, 6, 12, tzinfo=UTC),
        type=type_,
        scope=Scope(),
    )


def sample_registry() -> CommandRegistry:
    return CommandRegistry(
        [
            Command("approve", "Approve plan", Intent("approve"), key="a",
                    available=lambda s: s.slice("ready")),
            Command("cancel", "Cancel run", Intent("cancel", risky=True), key="c"),
            Command("diff", "Open diff", Intent("open_diff"), key="d"),
        ]
    )


def test_registry_rejects_duplicate_ids() -> None:
    with pytest.raises(ValueError, match="duplicate"):
        CommandRegistry(
            [
                Command("x", "X", Intent("x")),
                Command("x", "X2", Intent("x2")),
            ]
        )


def test_registry_preserves_declaration_order() -> None:
    reg = sample_registry()
    assert [c.id for c in reg.commands] == ["approve", "cancel", "diff"]


def test_registry_get() -> None:
    reg = sample_registry()
    assert reg.get("cancel").label == "Cancel run"


def test_risky_mirrors_intent() -> None:
    reg = sample_registry()
    assert reg.get("cancel").risky is True
    assert reg.get("diff").risky is False


def test_availability_derives_from_state() -> None:
    reg = sample_registry()
    store = make_store()
    assert reg.is_available("approve", store.snapshot) is False
    store.ingest(event("enable"))
    assert reg.is_available("approve", store.snapshot) is True


def test_default_availability_is_true() -> None:
    reg = sample_registry()
    assert reg.is_available("diff", make_store().snapshot) is True


# --- Matcher -----------------------------------------------------------------


def test_match_score_subsequence_case_insensitive() -> None:
    assert match_score("od", "Open diff") is not None
    assert match_score("OD", "open diff") is not None


def test_match_score_none_when_not_subsequence() -> None:
    assert match_score("zzz", "Open diff") is None


def test_match_score_prefers_contiguous_and_word_start() -> None:
    contiguous = match_score("open", "open diff")
    scattered = match_score("opn", "open diff")
    assert contiguous is not None and scattered is not None
    assert contiguous > scattered


def test_filter_commands_ranks_and_filters() -> None:
    reg = sample_registry()
    entries = command_view(reg)(make_store().snapshot).entries
    results = filter_commands(entries, "ca")
    assert [e.id for e in results] == ["cancel"]


def test_filter_commands_empty_query_returns_all_in_order() -> None:
    reg = sample_registry()
    entries = command_view(reg)(make_store().snapshot).entries
    results = filter_commands(entries, "")
    assert [e.id for e in results] == ["approve", "cancel", "diff"]


def test_filter_commands_matches_id_or_label() -> None:
    reg = sample_registry()
    entries = command_view(reg)(make_store().snapshot).entries
    # "plan" only appears in approve's label.
    assert [e.id for e in filter_commands(entries, "plan")] == ["approve"]


# --- command_view selector ---------------------------------------------------


def test_command_view_entries_mirror_registry() -> None:
    reg = sample_registry()
    view = command_view(reg)(make_store().snapshot)
    assert [e.id for e in view.entries] == ["approve", "cancel", "diff"]
    assert [e.key for e in view.entries] == ["a", "c", "d"]


def test_command_view_enabled_tracks_availability() -> None:
    reg = sample_registry()
    store = make_store()
    view = command_view(reg)
    before = {e.id: e.enabled for e in view(store.snapshot).entries}
    assert before["approve"] is False
    store.ingest(event("enable"))
    after = {e.id: e.enabled for e in view(store.snapshot).entries}
    assert after["approve"] is True


def test_command_view_memoized_per_snapshot() -> None:
    reg = sample_registry()
    view = command_view(reg)
    snap = make_store().snapshot
    assert view(snap) is view(snap)


def test_command_view_value_equality() -> None:
    reg = sample_registry()
    s1 = make_store().snapshot
    s2 = make_store().snapshot
    assert command_view(reg)(s1) == command_view(reg)(s2)
