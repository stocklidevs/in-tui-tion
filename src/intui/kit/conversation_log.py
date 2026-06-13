"""ConversationLog: a scrollable role/kind-tagged transcript (US2, R1).

Renders ``conversation_view`` in arrival order; each row is `‹tag› text` where
the tag carries role/kind textually (the non-color counterpart). Auto-scrolls
to keep the latest entries in view; shows an empty state.
"""

from __future__ import annotations

from typing import Any

from rich.text import Text
from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Static

from intui.kit.state.conversation import ConversationView
from intui.viewmodels.selector import Selector
from intui.widgets.bound import BoundContainer


class ConversationLog(BoundContainer):
    DEFAULT_CSS = """
    ConversationLog { height: auto; }
    ConversationLog #conv-scroll { height: auto; max-height: 100%; }
    ConversationLog #conv-body { padding: 0 1; }
    """

    def __init__(self, selector: Selector[ConversationView], **kwargs: Any) -> None:
        super().__init__(selector, **kwargs)
        self._view = ConversationView()

    def compose(self) -> ComposeResult:
        yield VerticalScroll(Static(id="conv-body"), id="conv-scroll")

    def sync_view(self, vm: ConversationView) -> None:
        self._view = vm
        self.query_one("#conv-body", Static).update(self._build_text())
        scroll = self.query_one("#conv-scroll", VerticalScroll)
        scroll.scroll_end(animate=False)

    def _build_text(self) -> Text:
        if not self._view.entries:
            return Text("no messages")
        theme = getattr(self.app, "intui_theme", None)
        muted = theme.resolve_color("muted") if theme is not None else None
        text = Text()
        for i, row in enumerate(self._view.entries):
            if i:
                text.append("\n")
            text.append(f"{row.tag}: ", style=(muted or ""))
            text.append(row.text)
        return text

    def log_text(self) -> str:
        return self._build_text().plain
