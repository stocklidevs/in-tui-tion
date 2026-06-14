"""Inspect artifacts: diffs and evidence, with redaction (engine-free).

Holds the artifact models, the unified-diff parser, the public-safety
redactor, the ``artifacts_slice()`` reduction of ``diff_ready``/
``evidence_ready``, and the ``diff_view``/``evidence_view`` selectors.

Redaction (Principle VI) lives here, in the pure layer, so it is headlessly
provable and applied by default — the selectors redact unless explicitly told
the context is trusted.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from enum import Enum
from types import MappingProxyType
from typing import Any

from intui.events.envelope import Event
from intui.state.snapshot import Snapshot
from intui.viewmodels.selector import Selector

REDACTION_MARKER = "‹redacted›"

#: Canonical event types the artifacts reducer consumes (stream contract).
ARTIFACT_EVENT_TYPES = frozenset({"diff_ready", "evidence_ready"})


# --- Models ------------------------------------------------------------------


class DiffLineKind(Enum):
    ADD = "add"
    REMOVE = "remove"
    CONTEXT = "context"


@dataclass(frozen=True, slots=True)
class DiffLine:
    kind: DiffLineKind
    text: str
    old_no: int | None = None
    new_no: int | None = None


@dataclass(frozen=True, slots=True)
class FileDiff:
    path: str
    raw_path: str
    added: int
    removed: int
    lines: tuple[DiffLine, ...] = ()
    no_text_diff: bool = False


@dataclass(frozen=True, slots=True)
class DiffArtifact:
    id: str
    title: str
    files: tuple[FileDiff, ...] = ()
    public_safe: bool = True


@dataclass(frozen=True, slots=True)
class EvidenceMetric:
    key: str
    label: str
    value: str | int | float | tuple[str, ...]
    status: str | None = None
    unsafe: bool = False


@dataclass(frozen=True, slots=True)
class EvidenceArtifact:
    id: str
    title: str
    metrics: tuple[EvidenceMetric, ...] = ()
    public_safe: bool = True


@dataclass(frozen=True, slots=True)
class ArtifactStore:
    diff: DiffArtifact | None = None
    evidence: EvidenceArtifact | None = None


# --- Redaction (Principle VI) ------------------------------------------------

_URL_CRED = re.compile(r"\w+://\S+")
_WIN_PATH = re.compile(r"[A-Za-z]:[\\/][^\s;]+")
# Absolute POSIX paths only: the leading "/" must not follow a word char, so a
# relative repo path (e.g. "src/integration_workbench/api.py") is NOT redacted —
# those are exactly what a diff/file view should show, and over-redacting them
# collapses distinct paths to one marker (see feature 011).
_POSIX_PATH = re.compile(r"(?<!\w)/(?:[\w.\-]+/)+[\w.\-]+")
_SK_TOKEN = re.compile(r"\bsk-[A-Za-z0-9]{6,}\b")
_HIGH_ENTROPY = re.compile(
    r"\b(?=[A-Za-z0-9_\-]*\d)(?=[A-Za-z0-9_\-]*[A-Za-z])[A-Za-z0-9_\-]{20,}\b"
)


def redact(text: str) -> str:
    """Replace recognizably-unsafe substrings with a redaction marker.

    Targets URLs (incl. embedded credentials), absolute local paths (Windows
    and POSIX), and token-like strings. Substring-wise, so an unsafe fragment
    inside a larger string is removed while the safe remainder survives.
    """
    for pattern in (_URL_CRED, _WIN_PATH, _POSIX_PATH, _SK_TOKEN, _HIGH_ENTROPY):
        text = pattern.sub(REDACTION_MARKER, text)
    return text


# --- Unified-diff parsing ----------------------------------------------------

_HUNK = re.compile(r"@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@")


def _strip_ab(path: str) -> str:
    if path.startswith(("a/", "b/")):
        return path[2:]
    return path


class _FileAcc:
    __slots__ = ("raw", "path", "add", "rem", "lines", "binary")

    def __init__(self) -> None:
        self.raw = ""
        self.path = ""
        self.add = 0
        self.rem = 0
        self.lines: list[DiffLine] = []
        self.binary = False

    def build(self) -> FileDiff:
        return FileDiff(
            path=self.path,
            raw_path=self.raw,
            added=self.add,
            removed=self.rem,
            lines=tuple(self.lines),
            no_text_diff=self.binary,
        )


def parse_unified_diff(text: str) -> tuple[FileDiff, ...]:
    """Parse unified-diff text into structured FileDiffs (tolerant, headless)."""
    files: list[FileDiff] = []
    cur: _FileAcc | None = None
    old_no: int | None = None
    new_no: int | None = None

    for line in text.splitlines():
        if line.startswith("--- "):
            if cur is not None:
                files.append(cur.build())
            cur = _FileAcc()
            old_no = new_no = None
            continue
        if line.startswith("+++ "):
            if cur is None:
                cur = _FileAcc()
            raw = _strip_ab(line[4:].strip())
            cur.raw = raw
            cur.path = raw.replace("\\", "/")
            continue
        if cur is None:
            continue
        if line.startswith("Binary files"):
            cur.binary = True
            continue
        if line.startswith("@@"):
            m = _HUNK.search(line)
            if m:
                old_no = int(m.group(1))
                new_no = int(m.group(2))
            continue
        if line.startswith("+"):
            cur.lines.append(DiffLine(DiffLineKind.ADD, line[1:], None, new_no))
            cur.add += 1
            if new_no is not None:
                new_no += 1
        elif line.startswith("-"):
            cur.lines.append(DiffLine(DiffLineKind.REMOVE, line[1:], old_no, None))
            cur.rem += 1
            if old_no is not None:
                old_no += 1
        else:
            body = line[1:] if line.startswith(" ") else line
            cur.lines.append(DiffLine(DiffLineKind.CONTEXT, body, old_no, new_no))
            if old_no is not None:
                old_no += 1
            if new_no is not None:
                new_no += 1

    if cur is not None:
        files.append(cur.build())
    return tuple(files)


# --- Reduction ---------------------------------------------------------------


def artifacts_slice() -> tuple[Any, ArtifactStore]:
    """``(reducer, initial)`` for ``compose_reducers(artifacts=artifacts_slice())``."""
    return _reduce, ArtifactStore()


def _reduce(state: ArtifactStore, event: Event) -> ArtifactStore:
    if event.type == "diff_ready":
        return replace(state, diff=_accumulate_diff(state.diff, event))
    if event.type == "evidence_ready":
        return replace(state, evidence=_build_evidence(event))
    return state


def _accumulate_diff(existing: DiffArtifact | None, event: Event) -> DiffArtifact:
    """Merge this ``diff_ready`` into the running diff artifact by path.

    Event streams are append-only facts ("this file changed"), so file diffs
    accumulate: a new path is appended (first-seen order), an already-seen path
    is replaced in place. A ``reset: true`` payload clears the accumulation first
    (a snapshot producer's opt-out). The latest event supplies id/title/safety.
    """
    incoming = _build_diff(event)
    reset = bool(event.payload.get("reset", False))
    if existing is None or reset:
        return incoming
    return replace(incoming, files=_merge_files(existing.files, incoming.files))


def _merge_files(old: tuple[FileDiff, ...], new: tuple[FileDiff, ...]) -> tuple[FileDiff, ...]:
    by_path: dict[str, FileDiff] = {}
    order: list[str] = []
    for file in (*old, *new):
        if file.raw_path not in by_path:
            order.append(file.raw_path)
        by_path[file.raw_path] = file
    return tuple(by_path[path] for path in order)


def _build_diff(event: Event) -> DiffArtifact:
    payload = event.payload
    title = str(payload.get("title", "diff"))
    public_safe = bool(payload.get("public_safe", True))
    unified = payload.get("unified")
    if isinstance(unified, str):
        files = parse_unified_diff(unified)
    else:
        files = tuple(_file_from_mapping(f) for f in payload.get("files", []))
    return DiffArtifact(id=event.event_id, title=title, files=files, public_safe=public_safe)


def _file_from_mapping(data: Mapping[str, Any]) -> FileDiff:
    raw = str(data.get("path", ""))
    lines = tuple(
        DiffLine(DiffLineKind(line.get("kind", "context")), str(line.get("text", "")))
        for line in data.get("lines", [])
    )
    added = sum(1 for line in lines if line.kind is DiffLineKind.ADD)
    removed = sum(1 for line in lines if line.kind is DiffLineKind.REMOVE)
    return FileDiff(
        path=raw.replace("\\", "/"),
        raw_path=raw,
        added=int(data.get("added", added)),
        removed=int(data.get("removed", removed)),
        lines=lines,
        no_text_diff=bool(data.get("no_text_diff", False)),
    )


def _build_evidence(event: Event) -> EvidenceArtifact:
    payload = event.payload
    metrics = tuple(_metric_from_mapping(m) for m in payload.get("metrics", []))
    return EvidenceArtifact(
        id=event.event_id,
        title=str(payload.get("title", "evidence")),
        metrics=metrics,
        public_safe=bool(payload.get("public_safe", True)),
    )


def _metric_from_mapping(data: Mapping[str, Any]) -> EvidenceMetric:
    value = data.get("value", "")
    if isinstance(value, (list, tuple)):
        value = tuple(str(v) for v in value)
    return EvidenceMetric(
        key=str(data.get("key", "")),
        label=str(data.get("label", data.get("key", ""))),
        value=value,
        status=data.get("status"),
        unsafe=bool(data.get("unsafe", False)),
    )


# --- View models + selectors -------------------------------------------------


@dataclass(frozen=True, slots=True)
class DiffFileRow:
    path: str
    added: int
    removed: int
    no_text_diff: bool


@dataclass(frozen=True, slots=True)
class DiffView:
    files: tuple[DiffFileRow, ...] = ()
    bodies: Mapping[str, tuple[DiffLine, ...]] = field(
        default_factory=lambda: MappingProxyType({})
    )

    def body(self, path: str) -> tuple[DiffLine, ...]:
        return self.bodies.get(path, ())

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, DiffView):
            return NotImplemented
        return self.files == other.files and dict(self.bodies) == dict(other.bodies)


@dataclass(frozen=True, slots=True)
class EvidenceRow:
    key: str
    label: str
    value: str
    status: str | None
    present: bool


@dataclass(frozen=True, slots=True)
class EvidenceView:
    rows: tuple[EvidenceRow, ...] = ()


def _board(snapshot: Snapshot, slice_name: str) -> ArtifactStore:
    return snapshot.slice(slice_name)  # type: ignore[no-any-return]


def diff_view(slice_name: str = "artifacts", *, public_safe: bool = True) -> Selector[DiffView]:
    def project(snapshot: Snapshot) -> DiffView:
        art = _board(snapshot, slice_name).diff
        if art is None:
            return DiffView()
        redacting = public_safe or not art.public_safe
        rows: list[DiffFileRow] = []
        bodies: dict[str, tuple[DiffLine, ...]] = {}
        for f in art.files:
            path = redact(f.path) if redacting else f.path
            rows.append(DiffFileRow(path, f.added, f.removed, f.no_text_diff))
            lines = (
                tuple(replace(line, text=redact(line.text)) for line in f.lines)
                if redacting
                else f.lines
            )
            bodies[path] = lines
        return DiffView(tuple(rows), MappingProxyType(bodies))

    return Selector(project)


def evidence_view(
    slice_name: str = "artifacts", *, public_safe: bool = True
) -> Selector[EvidenceView]:
    def project(snapshot: Snapshot) -> EvidenceView:
        art = _board(snapshot, slice_name).evidence
        if art is None:
            return EvidenceView()
        redacting = public_safe or not art.public_safe
        rows = tuple(_render_metric(m, redacting) for m in art.metrics)
        return EvidenceView(rows)

    return Selector(project)


def _render_metric(metric: EvidenceMetric, redacting: bool) -> EvidenceRow:
    rendered = ", ".join(metric.value) if isinstance(metric.value, tuple) else str(metric.value)
    if redacting:
        rendered = REDACTION_MARKER if metric.unsafe else redact(rendered)
    return EvidenceRow(
        key=metric.key,
        label=metric.label,
        value=rendered,
        status=metric.status,
        present=metric.value != "" and metric.value is not None,
    )
