"""Selectors: memoized pure projections from snapshots to view models."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, Generic, TypeVar

from intui.state.snapshot import Snapshot

VM = TypeVar("VM")


class Selector(Generic[VM]):
    """Memoized projection ``Snapshot -> VM``.

    Memoization is keyed by ``state_version``: re-invoking on the same version
    returns the cached view model without recomputation. View models must
    support value equality — the rendering layer uses it to decide whether a
    widget re-renders (FR-009, US1-2).
    """

    def __init__(self, fn: Callable[[Snapshot], VM]) -> None:
        self._fn = fn
        self._cached_snapshot: Snapshot | None = None
        self._cached_value: VM | None = None
        self.__name__ = getattr(fn, "__name__", "selector")

    def __call__(self, snapshot: Snapshot) -> VM:
        # Identity-keyed memoization: snapshots are immutable, so the same
        # object always projects to the same view model. Identity (not
        # state_version) keeps a shared selector safe across multiple stores.
        if snapshot is not self._cached_snapshot:
            self._cached_value = self._fn(snapshot)
            self._cached_snapshot = snapshot
        return self._cached_value  # type: ignore[return-value]


def selector(fn: Callable[[Snapshot], Any]) -> Selector[Any]:
    """Decorator turning a projection function into a memoized Selector."""
    return Selector(fn)
