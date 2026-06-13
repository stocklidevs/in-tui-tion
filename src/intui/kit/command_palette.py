"""CommandPalette: a searchable overlay over the command registry (US2, R7).

Lists every command, filters by a typed query (the in-house fuzzy matcher),
is keyboard-navigable, and invokes the selected command through the app's
``post_intent`` — so risky-action confirmation is inherited. The same registry
backs both this and the CommandBar (single source of truth).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Input, Static

from intui.kit.state.commands import CommandEntry, CommandRegistry, command_view, filter_commands

if TYPE_CHECKING:
    from intui.app import IntuiApp


class CommandPalette(ModalScreen[None]):
    BINDINGS = [
        Binding("escape", "dismiss_palette", "Close"),
        Binding("up", "move(-1)", "Up"),
        Binding("down", "move(1)", "Down"),
        Binding("enter", "run_selected", "Run"),
    ]

    DEFAULT_CSS = """
    CommandPalette { align: center top; }
    CommandPalette > Vertical {
        width: 60; max-width: 90%; height: auto; max-height: 80%;
        margin-top: 4; padding: 0; background: $surface; border: thick $primary;
    }
    CommandPalette Input { border: none; }
    CommandPalette #palette-results { height: auto; max-height: 16; }
    CommandPalette .palette-row { padding: 0 1; }
    CommandPalette .palette-selected { background: $primary; color: $text; }
    CommandPalette .palette-disabled { color: $text-muted; text-style: dim; }
    CommandPalette #palette-empty { padding: 0 1; color: $text-muted; }
    """

    def __init__(self, registry: CommandRegistry, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._registry = registry
        self._all: tuple[CommandEntry, ...] = ()
        self._results: tuple[CommandEntry, ...] = ()
        self._selected = 0
        self._invoked = False

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Input(placeholder="Type a command…", id="palette-query")
            yield VerticalScroll(Static(id="palette-list"), id="palette-results")
            yield Static("no matching commands", id="palette-empty")

    def on_mount(self) -> None:
        self._all = command_view(self._registry)(cast("IntuiApp", self.app).store.snapshot).entries
        self._results = self._all
        self._selected = 0
        self.query_one("#palette-query", Input).focus()
        self._refresh_list()

    # --- Query + selection ---------------------------------------------------

    def on_input_changed(self, event: Input.Changed) -> None:
        self._results = filter_commands(self._all, event.value)
        self._selected = 0
        self._refresh_list()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        # The focused Input swallows Enter; route it to run the selection.
        self.action_run_selected()

    def action_move(self, delta: int) -> None:
        if self._results:
            self._selected = (self._selected + delta) % len(self._results)
            self._refresh_list()

    def action_dismiss_palette(self) -> None:
        self.dismiss(None)

    def action_run_selected(self) -> None:
        if self._invoked or not self._results:
            return
        self._invoked = True
        command_id = self._results[self._selected].id
        app = cast("IntuiApp", self.app)
        self.dismiss(None)
        # Re-check availability against the current snapshot (FR-014).
        if not self._registry.is_available(command_id, app.store.snapshot):
            return
        # Defer until the palette has closed so a confirm prompt stacks cleanly.
        intent = self._registry.get(command_id).intent
        app.call_later(app.post_intent, intent)

    # --- Rendering -----------------------------------------------------------

    def _refresh_list(self) -> None:
        empty = not self._results
        self.query_one("#palette-empty").display = empty
        self.query_one("#palette-results").display = not empty
        if empty:
            return
        lines = []
        for i, entry in enumerate(self._results):
            marker = "›" if i == self._selected else " "  # non-color focus mark
            key = f"[{entry.key}]" if entry.key else "   "
            label = entry.label if entry.enabled else f"{entry.label} (off)"
            lines.append(f"{marker} {key} {label}")
        self.query_one("#palette-list", Static).update("\n".join(lines))

    # --- Introspection (apps and tests) -------------------------------------

    def result_ids(self) -> list[str]:
        return [e.id for e in self._results]

    def result_rows(self) -> list[str]:
        return [e.label for e in self._results]

    def is_empty_state(self) -> bool:
        return not self._results
