"""CommandBar: the always-visible bottom command menu (US1, R7).

Renders the primary commands from a CommandRegistry as a compact row of
`key label` entries. Keys (priority bindings, so they work app-wide) and
clicks invoke through the app's ``post_intent`` — inheriting risky-action
confirmation from feature 001. Unavailable commands render marked-disabled and
do not fire; availability is re-checked at fire time against the current
snapshot.
"""

from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING, Any, cast

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Static

from intui.kit.state.commands import CommandRegistry, CommandView, command_view
from intui.widgets.bound import BoundContainer

if TYPE_CHECKING:
    from intui.app import IntuiApp


class CommandBar(BoundContainer):
    DEFAULT_CSS = """
    CommandBar { height: 1; }
    CommandBar #cmd-row { height: 1; }
    CommandBar .cmd-entry { width: auto; padding: 0 1; }
    CommandBar .cmd-disabled { color: $text-muted; text-style: dim; }
    """

    def __init__(self, registry: CommandRegistry, **kwargs: Any) -> None:
        super().__init__(command_view(registry), **kwargs)
        self._registry = registry
        self._view = CommandView()

    def on_mount(self) -> None:
        super().on_mount()  # bridge registration (BoundContainer)
        # Command keys are app-global: register them through the app so they
        # fire regardless of which widget has focus.
        app = cast("IntuiApp", self.app)
        for command in self._registry.commands:
            if command.key:
                app.bind_key(
                    command.key,
                    partial(self._invoke, command.id),
                    description=command.label,
                )

    def compose(self) -> ComposeResult:
        # The registry is fixed at construction, so entry widgets are created
        # once here and only updated in place on refresh (no dynamic mounting).
        with Horizontal(id="cmd-row"):
            for command in self._registry.commands:
                yield Static(id=f"cmd-{command.id}", classes="cmd-entry")

    # --- BoundContainer contract --------------------------------------------

    def sync_view(self, vm: CommandView) -> None:
        self._view = vm
        for entry in vm.entries:
            widget = self.query_one(f"#cmd-{entry.id}", Static)
            widget.update(self._entry_text(entry.key, entry.label, entry.enabled))
            widget.set_class(not entry.enabled, "cmd-disabled")

    @staticmethod
    def _entry_text(key: str | None, label: str, enabled: bool) -> str:
        text = f"{key} {label}" if key else label
        return text if enabled else f"{text} (off)"  # non-color disabled marker

    # --- Invocation ----------------------------------------------------------

    def _invoke(self, command_id: str) -> None:
        app = cast("IntuiApp", self.app)
        # Re-check availability against the *current* snapshot (FR-014).
        if not self._registry.is_available(command_id, app.store.snapshot):
            return
        app.post_intent(self._registry.get(command_id).intent)

    def on_click(self, event: Any) -> None:
        node = getattr(event, "widget", None)
        while node is not None and node is not self:
            wid = getattr(node, "id", None)
            if wid and wid.startswith("cmd-") and wid != "cmd-row":
                self._invoke(wid[len("cmd-") :])
                return
            node = node.parent

    # --- Introspection (apps and tests) -------------------------------------

    def menu_text(self) -> str:
        return "  ".join((f"{e.key} {e.label}" if e.key else e.label) for e in self._view.entries)

    def is_enabled(self, command_id: str) -> bool:
        return any(e.id == command_id and e.enabled for e in self._view.entries)

    def entry_widget(self, command_id: str) -> Static:
        return self.query_one(f"#cmd-{command_id}", Static)
