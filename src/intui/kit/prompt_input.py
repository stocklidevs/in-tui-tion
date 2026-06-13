"""PromptInput: the persistent prompt surface (US1, R1).

Wraps the engine Input. On Enter with non-empty text it posts a
``prompt_submitted`` intent via the app and clears — it never mutates state
itself (Principle III); appending the user message is the application's job
(see ``prompt_message_event``).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Input

from intui.actions.intents import Intent

if TYPE_CHECKING:
    from intui.app import IntuiApp


class PromptInput(Widget):
    DEFAULT_CSS = """
    PromptInput { height: 3; }
    PromptInput Input { border: tall $panel; }
    """

    def __init__(self, *, placeholder: str = "type a goal…", **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._placeholder = placeholder

    def compose(self) -> ComposeResult:
        yield Input(placeholder=self._placeholder, id="prompt-field")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        text = event.value.strip()
        field = self.query_one("#prompt-field", Input)
        field.value = ""
        if not text:
            return  # no empty/whitespace submissions (FR-002)
        cast("IntuiApp", self.app).post_intent(Intent("prompt_submitted", {"text": text}))

    def focus_prompt(self) -> None:
        self.query_one("#prompt-field", Input).focus()
