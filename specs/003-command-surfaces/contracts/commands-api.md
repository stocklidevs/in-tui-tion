# Public API Contract: Command Surfaces

**Feature**: `003-command-surfaces` | **Date**: 2026-06-12

Extends the 001/002 contracts. Layer rule: `intui.kit.state` (incl. the new
`commands` module) imports no terminal engine; the surface widgets in
`intui.kit` may.

## `intui.kit.state` (engine-free additions)

```python
@dataclass(frozen=True)
class Command:
    id: str
    label: str
    intent: Intent                       # from intui.actions
    key: str | None = None
    available: Callable[[Snapshot], bool] = _always   # pure

    @property
    def risky(self) -> bool: ...         # == intent.risky

class CommandRegistry:
    def __init__(self, commands: Iterable[Command]): ...   # raises on dup id
    @property
    def commands(self) -> tuple[Command, ...]: ...
    def get(self, command_id: str) -> Command: ...
    def is_available(self, command_id: str, snapshot: Snapshot) -> bool: ...

@dataclass(frozen=True) class CommandEntry:
    id: str; label: str; key: str | None; risky: bool; enabled: bool

@dataclass(frozen=True) class CommandView:
    entries: tuple[CommandEntry, ...]

def command_view(registry: CommandRegistry) -> Selector[CommandView]

def match_score(query: str, text: str) -> int | None
def filter_commands(
    entries: Iterable[CommandEntry], query: str
) -> tuple[CommandEntry, ...]
```

## `intui.kit` (Textual layer)

```python
class CommandBar(BoundContainer):
    """Always-visible bottom menu of primary commands.

    Renders command_view(registry); invokes via the app's post_intent
    (risky-confirmation reused); disabled entries don't fire; overflow opens
    the palette.
    """
    def __init__(self, registry: CommandRegistry, **kwargs): ...

class CommandPalette(ModalScreen[None]):
    """Searchable overlay over the same registry.

    Filters by typed query, keyboard-selectable, invokes via post_intent,
    dismissable. Open with App.push_screen(CommandPalette(registry)).
    """
    def __init__(self, registry: CommandRegistry, **kwargs): ...
```

## `intui.app` (foundation addition)

```python
class IntuiApp(App[None]):
    def open_command_palette(self, registry: CommandRegistry) -> None
        # Convenience: push a CommandPalette for the given registry.
```

## Compatibility promises

- A command is declared once (`Command`) and rendered identically by both
  surfaces (SC-001) — the registry is the single source of truth.
- Invocation always flows through `post_intent`; risky commands always confirm
  first (FR-013). Library code never mutates app state.
- `match_score`/`filter_commands` are pure and stable — ranking is part of the
  contract and unit-tested.
