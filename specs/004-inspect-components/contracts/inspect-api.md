# Public API Contract: Inspect Components

**Feature**: `004-inspect-components` | **Date**: 2026-06-13

Extends 001/002/003. Layer rule: `intui.kit.state` (incl. the new `artifacts`
module) imports no terminal engine; the surface widgets in `intui.kit` may.

## `intui.kit.state` (engine-free additions)

```python
class DiffLineKind(Enum): ADD; REMOVE; CONTEXT

@dataclass(frozen=True) class DiffLine:
    kind: DiffLineKind; text: str; old_no: int | None = None; new_no: int | None = None

@dataclass(frozen=True) class FileDiff:
    path: str; raw_path: str; added: int; removed: int
    lines: tuple[DiffLine, ...] = (); no_text_diff: bool = False

@dataclass(frozen=True) class DiffArtifact:
    id: str; title: str; files: tuple[FileDiff, ...] = (); public_safe: bool = True

@dataclass(frozen=True) class EvidenceMetric:
    key: str; label: str; value: str | int | float | tuple[str, ...]
    status: str | None = None; unsafe: bool = False

@dataclass(frozen=True) class EvidenceArtifact:
    id: str; title: str; metrics: tuple[EvidenceMetric, ...] = (); public_safe: bool = True

@dataclass(frozen=True) class ArtifactStore:
    diff: DiffArtifact | None = None; evidence: EvidenceArtifact | None = None

def artifacts_slice() -> tuple[SliceReducer, ArtifactStore]
    # mount via compose_reducers(artifacts=artifacts_slice())

def parse_unified_diff(text: str) -> tuple[FileDiff, ...]
def redact(text: str) -> str

# View dataclasses + selector factories (public_safe defaults True):
@dataclass(frozen=True) class DiffFileRow:
    path: str; added: int; removed: int; no_text_diff: bool
@dataclass(frozen=True) class DiffView:
    files: tuple[DiffFileRow, ...]
    def body(self, path: str) -> tuple[DiffLine, ...]   # redacted lines for a file
@dataclass(frozen=True) class EvidenceRow:
    key: str; label: str; value: str; status: str | None; present: bool
@dataclass(frozen=True) class EvidenceView:
    rows: tuple[EvidenceRow, ...]

def diff_view(slice_name: str = "artifacts", *, public_safe: bool = True) -> Selector[DiffView]
def evidence_view(slice_name: str = "artifacts", *, public_safe: bool = True) -> Selector[EvidenceView]
```

## `intui.kit` (Textual layer)

```python
class DiffViewer(BoundContainer):
    """Changed-file list + selected-file green/red diff body.

    Keyboard file selection (engine list widget), scrollable diff body,
    selection preserved across refreshes by path; empty + no-text-diff states.
    """
    def __init__(self, selector: Selector[DiffView] = diff_view(), **kwargs): ...

class EvidencePanel(BoundContainer):
    """Labeled metric rows from the latest evidence artifact.

    List-valued metrics enumerate; status metrics show glyph+label; absent
    metrics show n/a; latest-artifact-wins.
    """
    def __init__(self, selector: Selector[EvidenceView] = evidence_view(), **kwargs): ...
```

## Compatibility promises

- Default rendering is public-safe (Principle VI): `diff_view`/`evidence_view`
  redact unless `public_safe=False` is passed explicitly.
- `parse_unified_diff` and `redact` are pure and stable — their behavior is
  part of the contract and unit-tested (SC-003/006).
- The `diff_ready`/`evidence_ready` mapping (data-model.md) is part of the
  contract; adding mappings is MINOR, changing existing ones MAJOR.
