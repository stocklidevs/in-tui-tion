"""ViewRouter: the central pane driven by the selected view (US1, R7).

A BoundContainer wrapping the engine's ContentSwitcher. The application
registers panes by id; the router binds to ``view_router_view`` and shows the
pane for the current selection, falling back to a placeholder when the
selection is empty or has no registered pane. Only the central pane changes on
selection; surrounding surfaces are untouched.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from textual.app import ComposeResult
from textual.containers import Container
from textual.widget import Widget
from textual.widgets import ContentSwitcher, Static

from intui.kit.state.views import ViewRouterView
from intui.viewmodels.selector import Selector
from intui.widgets.bound import BoundContainer

_PLACEHOLDER = "view-placeholder"


class ViewRouter(BoundContainer):
    DEFAULT_CSS = """
    ViewRouter { height: 1fr; }
    ViewRouter ContentSwitcher { height: 1fr; }
    ViewRouter #view-placeholder { color: $text-muted; padding: 1 2; }
    """

    def __init__(
        self,
        selector: Selector[ViewRouterView],
        views: Mapping[str, Widget],
        *,
        placeholder: str = "select a view",
        **kwargs: Any,
    ) -> None:
        super().__init__(selector, **kwargs)
        self._panes = dict(views)
        self._placeholder = placeholder
        self._view = ViewRouterView()

    def compose(self) -> ComposeResult:
        with ContentSwitcher(initial=_PLACEHOLDER):
            yield Static(self._placeholder, id=_PLACEHOLDER)
            for view_id, widget in self._panes.items():
                yield Container(widget, id=f"view-{view_id}")

    def sync_view(self, vm: ViewRouterView) -> None:
        self._view = vm
        switcher = self.query_one(ContentSwitcher)
        selected = next((e.id for e in vm.entries if e.selected), None)
        target = f"view-{selected}" if selected in self._panes else _PLACEHOLDER
        if switcher.current != target:
            switcher.current = target

    def current_view(self) -> str | None:
        return next((e.id for e in self._view.entries if e.selected), None)
