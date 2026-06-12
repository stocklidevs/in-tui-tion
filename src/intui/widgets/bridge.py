"""Store-to-Textual bridge with render coalescing (FR-012).

The bridge subscribes to the Store like any other consumer. Store publishes
mark the UI dirty; an idle-callback flush then refreshes bound widgets at
most once per burst, so rendering never queues unbounded work behind event
ingestion.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from intui.state.snapshot import Snapshot
from intui.state.store import Store

if TYPE_CHECKING:
    from textual.app import App

    from intui.widgets.bound import BoundWidget


class StoreBridge:
    def __init__(self, store: Store, app: App[Any]) -> None:
        self._store = store
        self._app = app
        self._widgets: list[BoundWidget] = []
        self._latest: Snapshot = store.snapshot
        self._flush_scheduled = False
        self._unsubscribe = store.subscribe(self._on_snapshot)

    def register(self, widget: BoundWidget) -> None:
        self._widgets.append(widget)
        widget.refresh_from(self._latest)

    def unregister(self, widget: BoundWidget) -> None:
        if widget in self._widgets:
            self._widgets.remove(widget)

    def shutdown(self) -> None:
        self._unsubscribe()
        self._widgets.clear()

    def _on_snapshot(self, snapshot: Snapshot) -> None:
        self._latest = snapshot
        if not self._flush_scheduled:
            self._flush_scheduled = True
            # Coalesce: any number of publishes before the callback runs
            # results in a single refresh against the latest snapshot.
            self._app.call_later(self._flush)

    def _flush(self) -> None:
        self._flush_scheduled = False
        for widget in self._widgets:
            widget.refresh_from(self._latest)
