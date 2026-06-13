# Quickstart: Command Surfaces

**Feature**: `003-command-surfaces` | **Date**: 2026-06-12

## Run the example

```sh
uv sync
uv run python -m examples.mission_control
```

The bottom command menu shows the primary actions; press a key to invoke one.
Press the palette shortcut (shown in the menu / footer) to open the searchable
palette, type to filter, and run any command. Risky commands ask to confirm.

## Declare commands once, render in both surfaces

```python
from intui.actions import Intent
from intui.kit import CommandBar, CommandPalette
from intui.kit.state import Command, CommandRegistry

registry = CommandRegistry([
    Command("approve", "Approve plan", Intent("approve"), key="a",
            available=lambda s: s.slice("run")["awaiting_approval"]),
    Command("cancel", "Cancel run", Intent("cancel", risky=True), key="c"),
    Command("diff", "Open diff", Intent("open_diff"), key="d"),
])

class MyApp(IntuiApp):
    def compose(self):
        ...
        yield CommandBar(registry)          # always-visible bottom menu

    def action_open_palette(self):
        self.open_command_palette(registry)  # same registry, searchable
```

Each command emits its `Intent` through the app's handler — risky ones confirm
first, unavailable ones disable themselves. No command mutates app state
directly.

## Test headlessly

```sh
uv run pytest tests/unit -k command       # registry, availability, matching
uv run pytest tests/snapshot -k "bar or palette"
```
