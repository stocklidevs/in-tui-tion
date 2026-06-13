"""IntuiApp: the application shell wiring pipeline, theme, and intents.

Foundation scope: store + source wiring with ingestion as an async task,
theme attachment, intent posting with the built-in risky-action confirmation
prompt, and the StoreBridge for coalesced rendering.
"""

from __future__ import annotations

from typing import Any

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.theme import Theme as TextualTheme
from textual.widgets import Label

from intui.actions.confirm import ConfirmationFlow
from intui.actions.intents import Intent, IntentHandler
from intui.events.sources import EventSource
from intui.state.store import Store
from intui.theming.default import DEFAULT_THEME
from intui.theming.theme import Theme
from intui.widgets.bridge import StoreBridge


def _to_textual_theme(theme: Theme) -> TextualTheme:
    """Map intui theme tokens onto Textual's design system (FR-017)."""
    muted = theme.emphasis.get("muted", "#808080")
    return TextualTheme(
        name=theme.name,
        primary=theme.emphasis.get("accent", "#0178d4"),
        accent=theme.emphasis.get("accent", "#0178d4"),
        background=theme.palette.get("background"),
        surface=theme.palette.get("surface"),
        panel=theme.palette.get("surface", muted),
        foreground=theme.palette.get("text"),
        success=theme.status_colors.get("success"),
        warning=theme.status_colors.get("waiting"),
        error=theme.status_colors.get("failure"),
        dark=True,
    )


class ConfirmScreen(ModalScreen[bool]):
    """Built-in confirmation prompt for risky intents (FR-016).

    Fully keyboard-operable: ``y``/``enter`` confirms, ``n``/``escape``
    cancels (Principle IV).
    """

    BINDINGS = [
        Binding("y,enter", "confirm", "Confirm"),
        Binding("n,escape", "cancel", "Cancel"),
    ]

    DEFAULT_CSS = """
    ConfirmScreen { align: center middle; }
    ConfirmScreen Vertical {
        width: auto; max-width: 60; height: auto;
        padding: 1 2; background: $surface; border: thick $warning;
    }
    """

    def __init__(self, intent: Intent) -> None:
        super().__init__()
        self.intent = intent

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label(f"Confirm risky action: [b]{self.intent.name}[/b]?")
            yield Label("y / enter = confirm    n / escape = cancel")

    def action_confirm(self) -> None:
        self.dismiss(True)

    def action_cancel(self) -> None:
        self.dismiss(False)


class IntuiApp(App[None]):
    """Base class for in-TUI-tion applications.

    Subclasses implement ``compose()`` (standard Textual composition) using
    :class:`~intui.widgets.bound.BoundWidget` subclasses; everything those
    widgets show derives from the store's snapshot (Principle I). User
    interactions route through :meth:`post_intent` to the application's
    handler — the library never mutates application state (Principle III).
    """

    def __init__(
        self,
        *,
        store: Store,
        source: EventSource | None = None,
        on_intent: IntentHandler | None = None,
        theme: Theme | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.store = store
        self._source = source
        self._on_intent = on_intent
        self.intui_theme = theme if theme is not None else DEFAULT_THEME
        self.bridge = StoreBridge(store, self)
        self._confirmation = ConfirmationFlow(deliver=self._deliver_intent)

    def on_mount(self) -> None:
        self.set_theme(self.intui_theme)
        if self._source is not None:
            self.run_worker(self._ingest(self._source), exclusive=False)

    def set_theme(self, theme: Theme) -> None:
        """Switch the application theme at runtime — no widget changes (FR-017)."""
        self.intui_theme = theme
        self.register_theme(_to_textual_theme(theme))
        self.theme = theme.name
        self.refresh_css()

    async def _ingest(self, source: EventSource) -> None:
        """Drive the source to completion without blocking rendering.

        Per-event failures are isolated by the store; source exhaustion is
        surfaced as stream health (FR-007), never as a crash.
        """
        await self.store.run(source)

    # --- Intents -----------------------------------------------------------

    def post_intent(self, intent: Intent) -> None:
        """Route a user interaction to the application as a named intent.

        Risky intents raise the built-in confirmation prompt before delivery;
        cancelled intents are never delivered.
        """
        was_pending = self._confirmation.pending is not None
        accepted = self._confirmation.submit(intent)
        if accepted and not was_pending and self._confirmation.pending is not None:
            self._show_confirmation(self._confirmation.pending)

    def _show_confirmation(self, intent: Intent) -> None:
        def on_result(confirmed: bool | None) -> None:
            if confirmed:
                self._confirmation.confirm()
            else:
                self._confirmation.cancel()

        self.push_screen(ConfirmScreen(intent), on_result)

    def _deliver_intent(self, intent: Intent) -> None:
        if self._on_intent is not None:
            self.run_worker(self._on_intent(intent), exclusive=False)
