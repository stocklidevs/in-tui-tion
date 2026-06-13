# Quickstart: Interactive Shell & Activity Strip

**Feature**: `006-interactive-shell` | **Date**: 2026-06-13

## Run the flagship

```sh
uv sync
uv run python -m examples.operator_console
```

A full-width KITT-style **activity strip** sweeps across the top in the run's
state color (red while working, cyan verifying, green passed, red strobe on
failure — with a textual label). At the bottom, a **prompt** awaits input: type
a goal, press Enter, and it appears in the conversation as your message while the
strip flashes "thinking" during the scripted reply. Everything is keyboard-first.

## Use the pieces

```python
from intui.kit import PromptInput, ActivityStrip
from intui.kit.state import activity_style, prompt_message_event
from intui.viewmodels import selector

@selector
def activity_state(snapshot):
    return snapshot.slice("run_status")   # -> "thinking" | "verifying" | ...

class Console(IntuiApp):
    def compose(self):
        yield ActivityStrip(activity_state)     # full-width, top
        ...
        yield PromptInput()                      # persistent, bottom

    async def handle_intent(self, intent):
        if intent.name == "prompt_submitted":
            self.store.ingest(prompt_message_event(intent.payload["text"]))
            # ... emit a reply / kick off work
```

The prompt emits `Intent("prompt_submitted", {"text": ...})`; mapping it to real
work is the application's (or adapter's) job. There is no live agent yet — the
example's reply is scripted, but the loop (input → intent → user message → agent
reply → transcript) is real.

## Test headlessly

```sh
uv run pytest tests/unit -k "activity or prompt"
uv run pytest tests/snapshot -k "prompt or activity or console"
```
