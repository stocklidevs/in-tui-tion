"""Widgets bound to view models.

A BoundWidget's only inputs are its view model and user interaction
(FR-010): it holds no authoritative state and re-renders only when the
view model's value actually changes.
"""

from __future__ import annotations

from typing import Any

from rich.console import RenderableType
from textual.widget import Widget
from textual.widgets import Static

from intui.state.snapshot import Snapshot
from intui.viewmodels.selector import Selector

_UNSET = object()


class _BindingMixin:
    """Selector binding + value-equality refresh, shared by both bound bases."""

    _selector: Selector[Any]
    _last_vm: Any

    def _bind(self, selector: Selector[Any]) -> None:
        self._selector = selector
        self._last_vm = _UNSET

    def refresh_from(self, snapshot: Snapshot) -> None:
        vm = self._selector(snapshot)
        if self._last_vm is not _UNSET and vm == self._last_vm:
            return  # value-equal view model: do not disturb this widget
        self._last_vm = vm
        self.apply_view(vm)

    def apply_view(self, vm: Any) -> None:
        raise NotImplementedError

    def _register(self) -> None:
        bridge = getattr(self.app, "bridge", None)  # type: ignore[attr-defined]
        if bridge is not None:
            bridge.register(self)

    def _unregister(self) -> None:
        bridge = getattr(self.app, "bridge", None)  # type: ignore[attr-defined]
        if bridge is not None:
            bridge.unregister(self)


class BoundWidget(_BindingMixin, Static):
    """Text widget bound to a Selector.

    Subclasses implement :meth:`render_view` to turn the view model into a
    renderable. ``refresh_from`` is driven by the StoreBridge.
    """

    def __init__(self, selector: Selector[Any], **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._bind(selector)

    def render_view(self, vm: Any) -> RenderableType:
        raise NotImplementedError

    def apply_view(self, vm: Any) -> None:
        self.update(self.render_view(vm))

    def on_mount(self) -> None:
        self._register()

    def on_unmount(self) -> None:
        self._unregister()


class BoundContainer(_BindingMixin, Widget):
    """Container widget bound to a Selector (kit components build on this).

    Same value-equality refresh contract as :class:`BoundWidget`, but
    subclasses implement :meth:`sync_view` to reconcile child widgets with
    the new view model instead of rendering text.
    """

    def __init__(self, selector: Selector[Any], **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._bind(selector)

    def sync_view(self, vm: Any) -> None:
        raise NotImplementedError

    def apply_view(self, vm: Any) -> None:
        self.sync_view(vm)

    def on_mount(self) -> None:
        self._register()

    def on_unmount(self) -> None:
        self._unregister()
