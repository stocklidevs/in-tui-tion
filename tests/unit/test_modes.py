"""Mode model: reduction, view, switch_mode_intent (engine-free)."""

from datetime import UTC, datetime

from intui.events import Event, Scope
from intui.kit.state import mode_slice, mode_view, switch_mode_intent
from intui.state import Store, compose_reducers

MODES = ("Plan", "Build", "Inspect", "Review")


def make_store(initial: str | None = None) -> Store:
    return Store(compose_reducers(modes=mode_slice(MODES, initial)))


def mode_changed(mode: str) -> Event:
    return Event(
        version="1",
        event_id=f"m-{mode}",
        run_id="r1",
        timestamp=datetime(2026, 6, 13, tzinfo=UTC),
        type="mode_changed",
        scope=Scope(),
        payload={"mode": mode},
    )


def test_initial_mode_is_first_by_default() -> None:
    store = make_store()
    assert store.snapshot.slice("modes").current == "Plan"


def test_initial_mode_can_be_seeded() -> None:
    store = make_store(initial="Build")
    assert store.snapshot.slice("modes").current == "Build"


def test_mode_changed_switches_current() -> None:
    store = make_store()
    store.ingest(mode_changed("Inspect"))
    assert store.snapshot.slice("modes").current == "Inspect"


def test_unknown_mode_ignored() -> None:
    store = make_store()
    store.ingest(mode_changed("Nonsense"))
    assert store.snapshot.slice("modes").current == "Plan"


def test_mode_view_entries_with_active_flag() -> None:
    store = make_store()
    store.ingest(mode_changed("Build"))
    view = mode_view()(store.snapshot)
    assert [e.name for e in view.entries] == list(MODES)
    active = [e.name for e in view.entries if e.active]
    assert active == ["Build"]


def test_switch_mode_intent_shape() -> None:
    intent = switch_mode_intent("Review")
    assert intent.name == "switch_mode"
    assert intent.payload == {"mode": "Review"}
    assert intent.risky is False


def test_mode_view_memoized_per_snapshot() -> None:
    store = make_store()
    view = mode_view()
    assert view(store.snapshot) is view(store.snapshot)


def test_switch_to_active_mode_is_noop() -> None:
    store = make_store(initial="Build")
    before = store.snapshot.slice("modes")
    store.ingest(mode_changed("Build"))
    assert store.snapshot.slice("modes") == before
