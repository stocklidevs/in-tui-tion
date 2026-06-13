"""Confirmation flow for risky intents (FR-016).

Lifecycle: ``created -> (confirming -> confirmed | cancelled) -> delivered``.
Non-risky intents skip the confirming states. While a confirmation is
pending, the prompt owns the interaction: further submissions are rejected
until the pending intent is resolved.
"""

from __future__ import annotations

from collections.abc import Callable

from intui.actions.intents import Intent

Deliver = Callable[[Intent], None]


class ConfirmationFlow:
    """Pure state machine; UI prompts subscribe via ``on_pending_changed``."""

    def __init__(
        self,
        deliver: Deliver,
        on_pending_changed: Callable[[Intent | None], None] | None = None,
    ) -> None:
        self._deliver = deliver
        self._on_pending_changed = on_pending_changed
        self._pending: Intent | None = None

    @property
    def pending(self) -> Intent | None:
        return self._pending

    def submit(self, intent: Intent) -> bool:
        """Submit an intent. Returns False if rejected (confirmation pending)."""
        if self._pending is not None:
            return False
        if intent.risky:
            self._set_pending(intent)
            return True
        self._deliver(intent)
        return True

    def confirm(self) -> None:
        """Deliver the pending intent. No-op when nothing is pending."""
        pending, self._pending = self._pending, None
        if pending is not None:
            self._notify()
            self._deliver(pending)

    def cancel(self) -> None:
        """Discard the pending intent — it is never delivered."""
        if self._pending is not None:
            self._pending = None
            self._notify()

    def _set_pending(self, intent: Intent) -> None:
        self._pending = intent
        self._notify()

    def _notify(self) -> None:
        if self._on_pending_changed is not None:
            self._on_pending_changed(self._pending)
