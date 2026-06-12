"""Contract-drift guard: the public API matches contracts/public-api.md.

If this test fails, either the contract or the implementation changed without
the other — update both together (and the examples: Principle VIII).
"""

import importlib

import pytest

# Names promised per module by the public API contract.
CONTRACT: dict[str, set[str]] = {
    "intui.events": {
        "Scope",
        "Event",
        "EnvelopeError",
        "parse_event",
        "StreamState",
        "StreamHealth",
        "EventSource",
        "MemorySource",
        "JsonlReplaySource",
        "write_recording",
        "read_recording",
    },
    "intui.state": {
        "Reducer",
        "compose_reducers",
        "Snapshot",
        "ReducerError",
        "Store",
    },
    "intui.viewmodels": {"selector", "Selector", "health_view"},
    "intui.actions": {"Intent", "IntentHandler"},
    "intui.theming": {"Theme", "DEFAULT_THEME"},
    # Rendering layer (imports the terminal engine):
    "intui.widgets": {"BoundWidget", "MotionMode", "StatusStyle", "Signal"},
    "intui.app": {"IntuiApp"},
}

CORE_MODULES = [m for m in CONTRACT if m not in ("intui.widgets", "intui.app")]


@pytest.mark.parametrize("module_name", list(CONTRACT))
def test_module_exposes_contract_names(module_name: str) -> None:
    module = importlib.import_module(module_name)
    missing = {name for name in CONTRACT[module_name] if not hasattr(module, name)}
    assert not missing, f"{module_name} missing contract names: {sorted(missing)}"


def test_root_package_reexports_the_engine_free_core() -> None:
    import intui

    expected = set().union(*(CONTRACT[m] for m in CORE_MODULES))
    missing = {name for name in expected if not hasattr(intui, name)}
    assert not missing, f"intui missing root re-exports: {sorted(missing)}"


def test_root_all_is_sorted_and_resolvable() -> None:
    import intui

    assert sorted(intui.__all__) == list(intui.__all__)
    for name in intui.__all__:
        assert getattr(intui, name) is not None
