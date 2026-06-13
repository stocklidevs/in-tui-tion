# Public API Contract: Interactive Shell & Activity Strip

**Feature**: `006-interactive-shell` | **Date**: 2026-06-13

Extends 001–005. Layer rule: `intui.kit.state` (new `activity` module + the
conversation helper) imports no terminal engine; the widgets in `intui.kit` may.

## `intui.kit.state` (engine-free additions)

```python
# Activity (intui.kit.state.activity)
ACTIVITY_STATES: tuple[str, ...]                 # thinking, waiting, verifying,
                                                 #   passed, history, failure, idle
ACTIVITY_STYLES: Mapping[str, StatusStyle]       # R6 mapping (engine-free types)
def activity_style(state: str) -> StatusStyle    # resolve with neutral fallback

# Conversation helper (intui.kit.state.conversation)
def prompt_message_event(text: str, run_id: str = "",
                         event_id: str | None = None) -> Event
    # role=user message_added event for a submitted prompt
```

## `intui.kit` (Textual layer)

```python
class PromptInput(Widget):
    """Persistent single-line prompt. Enter submits non-empty text as
    Intent("prompt_submitted", {"text": text}) via post_intent, then clears.
    """
    def __init__(self, *, placeholder: str = "type a goal…", **kwargs): ...

class ActivityStrip(Signal):
    """Full-width KITT-style activity indicator (R6) bound to a state selector.

    Uses ACTIVITY_STYLES; track length follows widget width (label kept on
    narrow terminals). State identifiable without color (glyph + label).
    """
    def __init__(self, selector: Selector[str], **kwargs): ...
```

## Compatibility promises

- The prompt emits `Intent("prompt_submitted", {"text": ...})`; the application
  maps it to work. The prompt never mutates state itself (Principle III).
- `prompt_message_event` builds the canonical user `message_added` event.
- `ACTIVITY_STYLES` is part of the contract (the R6 state→style mapping); adding
  states is MINOR, changing existing ones MAJOR.
- The `operator_console` example features both as first-class elements
  (Principle VIII).
```
