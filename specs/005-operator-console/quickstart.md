# Quickstart: Operator Console

**Feature**: `005-operator-console` | **Date**: 2026-06-13

## Run the flagship

```sh
uv sync
uv run python -m examples.operator_console
```

Replays a simulated agentic run. Switch modes with their keys (Plan/Build/
Inspect/Review — shown in the mode strip and command menu); read the
conversation transcript; in Build watch tasks, lanes, and the activity signal;
in Inspect read the diff and evidence (public-safe by default); `ctrl+p` opens
the command palette. Everything is keyboard-first.

## Use the new pieces

```python
from intui.kit import ModeStrip, ConversationLog
from intui.kit.state import (
    mode_slice, mode_view, switch_mode_intent,
    conversation_slice, conversation_view,
)
from intui.state import Store, compose_reducers

MODES = ("Plan", "Build", "Inspect", "Review")
store = Store(compose_reducers(
    modes=mode_slice(MODES),
    conversation=conversation_slice(),
    # ... taskboard, artifacts, etc.
))

class Console(IntuiApp):
    def compose(self):
        yield ModeStrip(mode_view(), keys={"1": "Plan", "2": "Build", "3": "Inspect", "4": "Review"})
        yield ConversationLog(conversation_view())

    async def handle_intent(self, intent):
        if intent.name == "switch_mode":
            # intent -> event -> state
            self.store.ingest(make_mode_changed(intent.payload["mode"]))
```

Emit `mode_changed`, `message_added` (with a `role`), `question_requested`,
and `approval_requested`; the kit reduces them with no custom reducers.

## Test headlessly

```sh
uv run pytest tests/unit -k "mode or conversation"
uv run pytest tests/snapshot -k "mode or conversation or console"
```
