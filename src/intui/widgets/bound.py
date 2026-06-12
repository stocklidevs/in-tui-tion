"""Widgets bound to view models.

A BoundWidget's only inputs are its view model and user interaction
(FR-010): it holds no authoritative state and re-renders only when the
view model's value actually changes.
"""

from __future__ import annotations

from typing import Any

from rich.console import RenderableType
from textual.widgets import Static

from intui.state.snapshot import Snapshot
from intui.viewmodels.selector import Selector

_UNSET = object()


class BoundWidget(Static):
    """Base widget bound to a Selector.

    Subclasses implement :meth:`render_view` to turn the view model into a
    renderable. ``refresh_from`` is driven by the StoreBridge.
    """

    def __init__(self, selector: Selector[Any], **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._selector = selector
        self._last_vm: Any = _UNSET

    def render_view(self, vm: Any) -> RenderableType:
        raise NotImplementedError

    def refresh_from(self, snapshot: Snapshot) -> None:
        vm = self._selector(snapshot)
        if self._last_vm is not _UNSET and vm == self._last_vm:
            return  # value-equal view model: do not disturb this widget
        self._last_vm = vm
        self.update(self.render_view(vm))

    def on_mount(self) -> None:
        bridge = getattr(self.app, "bridge", None)
        if bridge is not None:
            bridge.register(self)

    def on_unmount(self) -> None:
        bridge = getattr(self.app, "bridge", None)
        if bridge is not None:
            bridge.unregister(self)
