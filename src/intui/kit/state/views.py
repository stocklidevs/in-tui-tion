"""View-router model: the selected central view, switched via intent.

Engine-free, mirroring the mode model (005). Views are an ordered named set
with one selected member, reduced from ``view_selected`` events; selecting is a
``select_view`` intent the application turns into a ``view_selected`` event
(intent → event → state, Principle III). Independent of the mode model so the
two compose freely.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from typing import Any

from intui.actions.intents import Intent
from intui.events.envelope import Event
from intui.state.snapshot import Snapshot
from intui.viewmodels.selector import Selector


@dataclass(frozen=True, slots=True)
class ViewState:
    views: tuple[str, ...]
    current: str


@dataclass(frozen=True, slots=True)
class ViewEntry:
    id: str
    label: str
    selected: bool


@dataclass(frozen=True, slots=True)
class ViewRouterView:
    entries: tuple[ViewEntry, ...] = ()


def view_slice(views: Sequence[str], initial: str | None = None) -> tuple[Any, ViewState]:
    """``(reducer, initial)`` for ``compose_reducers(views=view_slice(...))``."""
    ordered = tuple(views)
    current = initial if initial in ordered else (ordered[0] if ordered else "")

    def reduce(state: ViewState, event: Event) -> ViewState:
        if event.type == "view_selected":
            target = event.payload.get("view")
            if isinstance(target, str) and target in state.views and target != state.current:
                return replace(state, current=target)
        return state

    return reduce, ViewState(views=ordered, current=current)


def view_router_view(
    slice_name: str = "views", labels: Mapping[str, str] | None = None
) -> Selector[ViewRouterView]:
    label_map = dict(labels or {})

    def project(snapshot: Snapshot) -> ViewRouterView:
        state: ViewState = snapshot.slice(slice_name)
        return ViewRouterView(
            entries=tuple(
                ViewEntry(
                    id=v,
                    label=label_map.get(v, v.replace("_", " ").title()),
                    selected=v == state.current,
                )
                for v in state.views
            )
        )

    return Selector(project)


def select_view_intent(view: str) -> Intent:
    """Build the intent that requests routing the center to ``view``."""
    return Intent("select_view", {"view": view})
