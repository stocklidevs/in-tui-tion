"""View-router model: reduction, selector, select_view_intent (engine-free)."""

from datetime import UTC, datetime

from intui.events import Event, Scope
from intui.kit.state import select_view_intent, view_router_view, view_slice
from intui.state import Store, compose_reducers

VIEWS = ("tasks", "lanes", "diff", "evidence")


def make_store(initial: str | None = None) -> Store:
    return Store(compose_reducers(views=view_slice(VIEWS, initial)))


def view_selected(view: str) -> Event:
    return Event(
        version="1",
        event_id=f"v-{view}",
        run_id="r1",
        timestamp=datetime(2026, 6, 13, tzinfo=UTC),
        type="view_selected",
        scope=Scope(),
        payload={"view": view},
    )


def test_initial_view_is_first_by_default() -> None:
    assert make_store().snapshot.slice("views").current == "tasks"


def test_initial_view_can_be_seeded() -> None:
    assert make_store(initial="diff").snapshot.slice("views").current == "diff"


def test_view_selected_switches_current() -> None:
    store = make_store()
    store.ingest(view_selected("evidence"))
    assert store.snapshot.slice("views").current == "evidence"


def test_unknown_view_ignored() -> None:
    store = make_store()
    store.ingest(view_selected("nonsense"))
    assert store.snapshot.slice("views").current == "tasks"


def test_view_router_view_entries_with_selected_flag() -> None:
    store = make_store()
    store.ingest(view_selected("diff"))
    view = view_router_view()(store.snapshot)
    assert [e.id for e in view.entries] == list(VIEWS)
    assert [e.id for e in view.entries if e.selected] == ["diff"]


def test_view_router_view_label_map() -> None:
    store = make_store()
    view = view_router_view(labels={"tasks": "Tasks & plan"})(store.snapshot)
    tasks = next(e for e in view.entries if e.id == "tasks")
    assert tasks.label == "Tasks & plan"
    # default label is the id title-cased
    diff = next(e for e in view.entries if e.id == "diff")
    assert diff.label == "Diff"


def test_select_view_intent_shape() -> None:
    intent = select_view_intent("evidence")
    assert intent.name == "select_view"
    assert intent.payload == {"view": "evidence"}
    assert intent.risky is False


def test_view_router_view_memoized() -> None:
    store = make_store()
    view = view_router_view()
    assert view(store.snapshot) is view(store.snapshot)
