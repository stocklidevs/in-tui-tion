# Public API Contract: Core Library Foundation

**Feature**: `001-core-library-foundation` | **Date**: 2026-06-12

This is the contract the example (and all future layers) program against.
Names below are the stable public surface for this feature; everything else
in `intui.*` is private. Signatures are contractual in shape (names,
parameters, semantics), not in exact typing syntax.

Layer rule (Principle II): `intui.events`, `intui.state`, `intui.viewmodels`,
`intui.actions`, `intui.theming` import no terminal engine. Only
`intui.widgets` and `intui.app` touch Textual.

## `intui.events`

```python
@dataclass(frozen=True)
class Scope:
    session_id: str | None = None
    task_id: str | None = None
    work_item_id: str | None = None
    lane_id: str | None = None
    extra: Mapping[str, str] = ...   # adapter-specific keys

@dataclass(frozen=True)
class Event:
    version: str            # "1"
    event_id: str
    run_id: str
    timestamp: datetime     # UTC
    type: str
    scope: Scope
    status: str | None = None
    summary: str | None = None
    payload: Mapping[str, Any] = ...

class EnvelopeError(Exception):
    """Raised/reported when an envelope fails validation; carries event_id
    (if known), line number (for recordings), and reason."""

def parse_event(data: Mapping[str, Any]) -> Event
    # Validates against envelope schema v1; raises EnvelopeError.

class StreamState(Enum): LIVE; ENDED; DISCONNECTED; ERRORING

@dataclass(frozen=True)
class StreamHealth:
    state: StreamState
    last_event_at: datetime | None
    rejected_count: int
    last_error: EnvelopeError | ReducerError | None

class EventSource(Protocol):
    """Async iterator of raw envelope mappings + terminal outcome."""
    def __aiter__(self) -> AsyncIterator[Mapping[str, Any]]: ...

class MemorySource(EventSource):
    def __init__(self, events: Iterable[Event | Mapping[str, Any]]): ...

class JsonlReplaySource(EventSource):
    def __init__(self, path: Path, *,
                 rate: float | None = None,        # events/sec; None = as fast as possible
                 on_malformed: Literal["skip", "halt"] = "skip"): ...

def write_recording(path: Path, events: Iterable[Event]) -> None
def read_recording(path: Path, *,
                   on_malformed: Literal["skip", "halt"] = "skip") -> list[Event]
```

## `intui.state`

```python
class Reducer(Protocol):
    def __call__(self, snapshot: Snapshot, event: Event) -> Snapshot: ...
    # MUST be pure; MUST return snapshot unchanged for unknown types.

def compose_reducers(**slice_reducers: SliceReducer) -> Reducer
    # Each reducer owns a named state slice.

@dataclass(frozen=True)
class Snapshot:
    state_version: int
    health: StreamHealth
    def slice(self, name: str) -> Any            # app-defined immutable slice
    # Structural equality: same event sequence => equal snapshots.

class ReducerError(Exception):
    """Reported when a reducer raises; carries event_id and cause.
    The store retains the prior snapshot."""

class Store:
    def __init__(self, reducer: Reducer, initial: Snapshot | None = None): ...
    @property
    def snapshot(self) -> Snapshot: ...
    def ingest(self, event: Event) -> None       # validate, dedupe, reduce, publish
    def subscribe(self, callback: Callable[[Snapshot], None]) -> Unsubscribe: ...
    async def run(self, source: EventSource) -> StreamHealth
        # Drives a source to completion; never raises for per-event failures.
```

## `intui.viewmodels`

```python
def selector(fn: Callable[[Snapshot], VM]) -> Selector[VM]
    # Memoized per state_version; VM must support value equality.

health_view: Selector[HealthView]   # built-in stream-health view model
```

## `intui.actions`

```python
@dataclass(frozen=True)
class Intent:
    name: str
    payload: Mapping[str, Any] = ...
    risky: bool = False

class IntentHandler(Protocol):
    async def __call__(self, intent: Intent) -> None: ...
    # The application's seam: typically appends new events. The library
    # never mutates application state itself.
```

Semantics: intents with `risky=True` are held by the app shell until the
user explicitly confirms (built-in confirmation prompt); cancelled intents
are never delivered.

## `intui.theming`

```python
@dataclass(frozen=True)
class Theme:
    name: str
    palette: Mapping[str, str]        # background/surface/text tiers
    emphasis: Mapping[str, str]       # accent/muted
    status_colors: Mapping[str, str]  # status name -> color token

DEFAULT_THEME: Theme                  # shipped default (dark)
```

## `intui.widgets` (Textual layer)

```python
class BoundWidget(Widget):
    """Base widget bound to a Selector; re-renders only when its view model
    value changes. Subclasses implement render_view(vm)."""
    def __init__(self, selector: Selector[VM], ...): ...

class MotionMode(Enum): STEADY; PULSE; SWOOSH; STROBE

@dataclass(frozen=True)
class StatusStyle:
    color: str            # theme status-color token
    motion: MotionMode
    glyph: str            # mandatory non-color counterpart
    label: str            # mandatory textual counterpart

class Signal(BoundWidget):
    """Status-driven indicator. Appearance derives exclusively from the
    bound status field; never set directly."""
    def __init__(self, selector: Selector[str],
                 styles: Mapping[str, StatusStyle], ...): ...
```

## `intui.app`

```python
class IntuiApp(App):
    """Application shell wiring store, theme, intents, and key bindings.

    - compose() is app-defined (standard Textual composition with
      BoundWidget/Signal instances).
    - Ingestion runs as an async task; rendering is coalesced so the UI
      never blocks on event bursts.
    - Every primary action gets a keybinding; risky intents trigger the
      built-in confirmation flow before reaching the handler.
    """
    def __init__(self, *,
                 store: Store,
                 source: EventSource,
                 on_intent: IntentHandler,
                 theme: Theme = DEFAULT_THEME): ...
    def set_theme(self, theme: Theme) -> None     # runtime switch, no widget changes
    def post_intent(self, intent: Intent) -> None # widgets route intents here
```

## Compatibility promises (this feature)

- Envelope schema v1 is frozen by `event-envelope.schema.json`; changes
  require a new envelope version and follow semantic-versioning discipline.
- Recordings written by `write_recording` are readable by `read_recording`
  and `JsonlReplaySource` losslessly.
- A breaking change to any name above is not complete until the examples
  gallery is updated (Constitution Principle VIII).
