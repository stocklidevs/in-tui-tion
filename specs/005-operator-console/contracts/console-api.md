# Public API Contract: Operator Console

**Feature**: `005-operator-console` | **Date**: 2026-06-13

Extends 001–004. Layer rule: `intui.kit.state` (new `modes`, `conversation`
modules) imports no terminal engine; the surface widgets in `intui.kit` may.

## `intui.kit.state` (engine-free additions)

```python
# Modes
@dataclass(frozen=True) class ModeState:
    modes: tuple[str, ...]; current: str
@dataclass(frozen=True) class ModeEntry:
    name: str; active: bool
@dataclass(frozen=True) class ModeView:
    entries: tuple[ModeEntry, ...]

def mode_slice(modes: Sequence[str], initial: str | None = None
              ) -> tuple[SliceReducer, ModeState]
def mode_view(slice_name: str = "modes") -> Selector[ModeView]
def switch_mode_intent(mode: str) -> Intent          # Intent("switch_mode", {"mode": mode})

# Conversation
class ConversationKind(Enum): MESSAGE; QUESTION; APPROVAL
@dataclass(frozen=True) class ConversationEntry:
    order: int; role: str; kind: ConversationKind; text: str
@dataclass(frozen=True) class ConversationState:
    entries: tuple[ConversationEntry, ...] = ()
@dataclass(frozen=True) class ConversationRow:
    order: int; role: str; kind: ConversationKind; text: str; tag: str
@dataclass(frozen=True) class ConversationView:
    entries: tuple[ConversationRow, ...] = ()

def conversation_slice() -> tuple[SliceReducer, ConversationState]
def conversation_view(slice_name: str = "conversation") -> Selector[ConversationView]
```

## `intui.kit` (Textual layer)

```python
class ModeStrip(BoundContainer):
    """Row of modes, active one marked; each mode's key posts switch_mode.

    Keys registered through IntuiApp.bind_key (app-global). Renders mode_view.
    """
    def __init__(self, selector: Selector[ModeView] = mode_view(),
                 keys: Mapping[str, str] | None = None, **kwargs): ...
        # keys maps a shortcut -> mode name (optional)

class ConversationLog(BoundContainer):
    """Scrollable role/kind-tagged transcript; auto-scrolled to latest."""
    def __init__(self, selector: Selector[ConversationView] = conversation_view(), **kwargs): ...
```

## Compatibility promises

- Mode switching flows intent → `mode_changed` event → state (Principle III);
  `switch_mode_intent` is the stable way to build the intent.
- The `mode_changed` / `message_added` / `question_requested` /
  `approval_requested` mappings (data-model.md) are part of the contract;
  adding mappings is MINOR, changing existing ones MAJOR.
- The `operator_console` example is a first-class deliverable (Principle VIII),
  runnable from a fresh checkout.
