# Public API Contract: Stream Contract & Packaging

**Feature**: `008-stream-contract-packaging` | **Date**: 2026-06-13

## `intui.events` (engine-free additions)

```python
@dataclass(frozen=True) class StreamIssue:
    line: int
    severity: str          # "error" | "warning"
    reason: str
    event_id: str | None = None

def validate_event(
    data: Mapping[str, Any], *, known_types: Collection[str] | None = None
) -> list[StreamIssue]

def validate_stream(
    lines: Iterable[str] | Path | str, *,
    known_types: Collection[str] | None = None,
    event_record_types: tuple[str, ...] = (),
) -> list[StreamIssue]
```

## `intui.kit.state` (engine-free additions)

```python
TASKBOARD_EVENT_TYPES: frozenset[str]
ARTIFACT_EVENT_TYPES: frozenset[str]
CONVERSATION_EVENT_TYPES: frozenset[str]
MODE_EVENT_TYPES: frozenset[str]
VIEW_EVENT_TYPES: frozenset[str]
KNOWN_EVENT_TYPES: frozenset[str]   # union of all of the above
```

## Published artifacts (repo)

- `docs/contracts/event-envelope.schema.json` — canonical envelope JSON Schema.
- `docs/event-stream-contract.md` — the single source of truth for the
  vocabulary + payload conventions + public-safety guidance.
- `docs/quickstart.md` — stream-first + build-in-code onboarding.

## Packaging

- `pyproject.toml` `[project]` with dynamic version from
  `src/intui/__init__.py`, full metadata, classifiers, urls.
- `src/intui/py.typed` (PEP 561).
- Buildable wheel (`uv build`) installable into a clean env with `import intui`.

## Compatibility promises

- `KNOWN_EVENT_TYPES` is the canonical vocabulary; adding a type is MINOR,
  removing one MAJOR. Each module's `*_EVENT_TYPES` is the source the matching
  reducer uses, so the registry cannot drift from behavior.
- `validate_event`/`validate_stream` are pure and stable; unknown types are
  warnings (runtime tolerates them), envelope problems are errors.
- `intui.__version__` is the single version source.
