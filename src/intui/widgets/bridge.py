"""Store-to-Textual bridge with render coalescing (FR-012).

The bridge subscribes to the Store like any other consumer. Store publishes
mark the UI dirty; flushes are throttled with a leading edge — an idle store
renders immediately, while sustained event streams are batched to at most
``max_fps`` refreshes per second — so rendering never queues unbounded work
behind ingestion, however fast events arrive.
"""

from __future__ import annotations

from time import monotonic
from typing import TYPE_CHECKING, Any

from intui.state.snapshot import Snapshot
from intui.state.store import Store

if TYPE_CHECKING:
    from textual.app import App

    from intui.widgets.bound import BoundWidget


class StoreBridge:
    def __init__(self, store: Store, app: App[Any], *, max_fps: float = 30.0) -> None:
        self._store = store
        self._app = app
        self._widgets: list[BoundWidget] = []
        self._latest: Snapshot = store.snapshot
        self._held: Snapshot | None = None
        self._flush_scheduled = False
        self._min_interval = 1.0 / max_fps
        self._last_flush = 0.0
        self._unsubscribe = store.subscribe(self._on_snapshot)

    def register(self, widget: BoundWidget) -> None:
        self._widgets.append(widget)
        widget.refresh_from(self._held if self._held is not None else self._latest)

    def hold(self, snapshot: Snapshot) -> None:
        """Render a held (historical) snapshot and freeze live flushing.

        Live publishes keep updating the tracked latest so :meth:`release` is
        immediate; the rendered view stays at ``snapshot`` until released.
        """
        self._held = snapshot
        self._render_now()

    def release(self) -> None:
        """Resume rendering the latest live snapshot."""
        self._held = None
        self._render_now()

    def _render_now(self) -> None:
        target = self._held if self._held is not None else self._latest
        for widget in self._widgets:
            widget.refresh_from(target)

    def unregister(self, widget: BoundWidget) -> None:
        if widget in self._widgets:
            self._widgets.remove(widget)

    def shutdown(self) -> None:
        self._unsubscribe()
        self._widgets.clear()

    def _on_snapshot(self, snapshot: Snapshot) -> None:
        self._latest = snapshot
        if self._held is not None:
            return  # view is frozen on a held snapshot; track latest only
        if self._flush_scheduled:
            # Coalesce: any number of publishes before the pending flush
            # runs results in a single refresh against the latest snapshot.
            return
        self._flush_scheduled = True
        elapsed = monotonic() - self._last_flush
        if elapsed >= self._min_interval:
            self._app.call_later(self._flush)  # idle: render immediately
        else:
            self._app.set_timer(self._min_interval - elapsed, self._flush)

    def _flush(self) -> None:
        self._flush_scheduled = False
        self._last_flush = monotonic()
        target = self._held if self._held is not None else self._latest
        for widget in self._widgets:
            widget.refresh_from(target)
