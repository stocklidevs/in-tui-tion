"""in-TUI-tion: a library for rich, first-class terminal user interfaces.

The engine-free pipeline core is re-exported here (``import intui`` pulls in
no terminal engine). The rendering layer lives in :mod:`intui.widgets` and
:mod:`intui.app` — import those explicitly when building a UI.

Public API contract: specs/001-core-library-foundation/contracts/public-api.md
"""

from intui.actions import ConfirmationFlow, Intent, IntentHandler
from intui.emit import RunRecorder, run_recorder
from intui.events import (
    EnvelopeError,
    Event,
    EventSource,
    EventStream,
    JsonlReplaySource,
    MemorySource,
    Scope,
    StreamError,
    StreamHealth,
    StreamIssue,
    StreamState,
    parse_event,
    read_recording,
    validate_event,
    validate_stream,
    write_recording,
)
from intui.state import Reducer, ReducerError, SliceReducer, Snapshot, Store, compose_reducers
from intui.theming import (
    DEFAULT_THEME,
    MotionMode,
    StatusStyle,
    Theme,
    resolve_status_style,
)
from intui.viewmodels import HealthView, Selector, health_view, selector

__version__ = "0.17.0"

__all__ = [
    "ConfirmationFlow",
    "DEFAULT_THEME",
    "EnvelopeError",
    "Event",
    "EventSource",
    "EventStream",
    "HealthView",
    "Intent",
    "IntentHandler",
    "JsonlReplaySource",
    "MemorySource",
    "MotionMode",
    "Reducer",
    "ReducerError",
    "RunRecorder",
    "Scope",
    "Selector",
    "SliceReducer",
    "Snapshot",
    "StatusStyle",
    "Store",
    "StreamError",
    "StreamHealth",
    "StreamIssue",
    "StreamState",
    "Theme",
    "compose_reducers",
    "health_view",
    "parse_event",
    "read_recording",
    "resolve_status_style",
    "run_recorder",
    "selector",
    "validate_event",
    "validate_stream",
    "write_recording",
]
