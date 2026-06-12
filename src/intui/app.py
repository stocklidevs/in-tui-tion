"""IntuiApp: the application shell wiring pipeline, theme, and (later) intents.

Foundation scope: store + source wiring with ingestion as an async task,
theme attachment, and the StoreBridge for coalesced rendering. Intent
delivery and runtime theme switching land in their dedicated user stories.
"""

from __future__ import annotations

from typing import Any

from textual.app import App

from intui.events.sources import EventSource
from intui.state.store import Store
from intui.theming.default import DEFAULT_THEME
from intui.theming.theme import Theme
from intui.widgets.bridge import StoreBridge


class IntuiApp(App[None]):
    """Base class for in-TUI-tion applications.

    Subclasses implement ``compose()`` (standard Textual composition) using
    :class:`~intui.widgets.bound.BoundWidget` subclasses; everything those
    widgets show derives from the store's snapshot (Principle I).
    """

    def __init__(
        self,
        *,
        store: Store,
        source: EventSource | None = None,
        theme: Theme | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.store = store
        self._source = source
        self.intui_theme = theme if theme is not None else DEFAULT_THEME
        self.bridge = StoreBridge(store, self)

    def on_mount(self) -> None:
        if self._source is not None:
            self.run_worker(self._ingest(self._source), exclusive=False)

    async def _ingest(self, source: EventSource) -> None:
        """Drive the source to completion without blocking rendering.

        Per-event failures are isolated by the store; source exhaustion is
        surfaced as stream health (FR-007), never as a crash.
        """
        await self.store.run(source)
