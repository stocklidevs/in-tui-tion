"""Workspace model: a file tree reduced from ``file_*`` events (engine-free).

A run that creates code emits ``file_written``/``file_removed``; this reduces
them into a flat, normalized-path file set, and ``file_tree_view`` projects that
into a nested directory tree (directories inferred from path segments). Rendered
by the ``FileTree`` widget. Public-safe by default (paths redacted), like the
diff/evidence views.

``scan_workspace`` is a side-effecting convenience that walks a real directory
and yields ``file_written`` events with relative paths — engine-free (stdlib
only) but impure (reads the FS), kept separate from the replayable core.
"""

from __future__ import annotations

import os
from collections.abc import Iterator, Mapping
from dataclasses import dataclass, field, replace
from pathlib import Path
from types import MappingProxyType
from typing import Any

from intui.actions.intents import Intent
from intui.events.envelope import Event, Scope
from intui.kit.state.artifacts import redact
from intui.state.snapshot import Snapshot
from intui.viewmodels.selector import Selector

#: Canonical workspace event types (stream contract).
WORKSPACE_EVENT_TYPES = frozenset({"file_written", "file_removed"})

_FILE_GLYPHS = {"added": "+", "modified": "~"}
_DIR_GLYPH = "/"


def _normalize(path: str) -> str:
    """Normalize a path for keying: ``\\``→``/``, strip ``./`` and edges."""
    norm = path.replace("\\", "/").strip()
    while norm.startswith("./"):
        norm = norm[2:]
    return norm.strip("/")


# --- Models ------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class FileEntry:
    path: str
    status: str  # "added" | "modified"


def _empty_files() -> Mapping[str, FileEntry]:
    return MappingProxyType({})


@dataclass(frozen=True, slots=True)
class WorkspaceState:
    files: Mapping[str, FileEntry] = field(default_factory=_empty_files)


@dataclass(frozen=True, slots=True)
class FileNode:
    name: str
    path: str
    is_dir: bool
    status: str = ""
    glyph: str = ""
    children: tuple[FileNode, ...] = ()


@dataclass(frozen=True, slots=True)
class FileTreeView:
    roots: tuple[FileNode, ...] = ()


# --- Reduction ---------------------------------------------------------------


def workspace_slice() -> tuple[Any, WorkspaceState]:
    """``(reducer, initial)`` for ``compose_reducers(workspace=workspace_slice())``."""
    return _reduce, WorkspaceState()


def _reduce(state: WorkspaceState, event: Event) -> WorkspaceState:
    if event.type == "file_written":
        path = _normalize(str(event.payload.get("path", "")))
        if not path:
            return state
        change_type = event.payload.get("change_type")
        if change_type in ("added", "modified"):
            status = str(change_type)
        else:
            status = "modified" if path in state.files else "added"
        return replace(state, files={**state.files, path: FileEntry(path, status)})
    if event.type == "file_removed":
        path = _normalize(str(event.payload.get("path", "")))
        if path not in state.files:
            return state
        files = dict(state.files)
        del files[path]
        return replace(state, files=files)
    return state


# --- Tree view model ---------------------------------------------------------


def file_tree_view(
    slice_name: str = "workspace", *, public_safe: bool = True
) -> Selector[FileTreeView]:
    """Project the flat file set into a nested directory tree (public-safe)."""

    def project(snapshot: Snapshot) -> FileTreeView:
        state: WorkspaceState = snapshot.slice(slice_name)
        root: dict[str, Any] = {}
        for entry in state.files.values():
            real = entry.path  # normalized, real path (used for actions)
            display = redact(real) if public_safe else real
            # Unsafe path: a single leaf whose display name is the redacted form
            # but which still carries the real path (so an action targets the
            # actual file) — we don't reveal an unsafe path's structure.
            segments = [display] if display != real else [s for s in real.split("/") if s]
            if not segments:
                continue
            _insert(root, segments, real, entry.status)
        return FileTreeView(roots=_build_nodes(root))

    return Selector(project)


def _insert(node: dict[str, Any], segments: list[str], real_path: str, status: str) -> None:
    cur = node
    acc = ""
    last = len(segments) - 1
    for i, seg in enumerate(segments):
        acc = f"{acc}/{seg}" if acc else seg
        child = cur.setdefault(
            seg, {"__dir__": False, "__status__": "", "__path__": acc, "__children__": {}}
        )
        if i == last:
            # the file leaf (a later write under the same name wins its status)
            child["__status__"] = status
            child["__path__"] = real_path
        else:
            child["__dir__"] = True
            cur = child["__children__"]


def _build_nodes(node: dict[str, Any]) -> tuple[FileNode, ...]:
    nodes: list[FileNode] = []
    for name, data in node.items():
        is_dir = bool(data["__dir__"])
        children = _build_nodes(data["__children__"]) if is_dir else ()
        status = "" if is_dir else str(data["__status__"])
        glyph = _DIR_GLYPH if is_dir else _FILE_GLYPHS.get(status, "")
        nodes.append(FileNode(name, str(data["__path__"]), is_dir, status, glyph, children))
    # dirs before files, then alphabetical by name
    nodes.sort(key=lambda n: (not n.is_dir, n.name))
    return tuple(nodes)


# --- File-action intents (Principle III: the app fulfills; we only request) --


def open_file_intent(path: str) -> Intent:
    """Request opening ``path`` (the app decides how)."""
    return Intent("open_file", {"path": path})


def copy_path_intent(path: str) -> Intent:
    """Request copying ``path`` (e.g. to the clipboard)."""
    return Intent("copy_path", {"path": path})


def delete_file_intent(path: str) -> Intent:
    """Request deleting ``path`` — risky, so it is confirmed before delivery."""
    return Intent("delete_file", {"path": path}, risky=True)


# --- Live convenience (impure) -----------------------------------------------


def scan_workspace(root: Path | str, *, run_id: str = "workspace") -> Iterator[Event]:
    """Walk ``root`` and yield ``file_written`` events with relative paths.

    Side-effecting (reads the filesystem) and one-shot — feed it via
    ``MemorySource(scan_workspace(root))``. Paths are relative to ``root`` and
    normalized, keeping the resulting tree public-safe and portable.
    """
    base = Path(root)
    seq = 0
    for dirpath, _dirs, files in os.walk(base):
        for name in sorted(files):
            rel = _normalize(str(Path(dirpath, name).relative_to(base)))
            seq += 1
            yield Event(
                version="1",
                event_id=f"scan-{seq}",
                run_id=run_id,
                timestamp=_fixed_time(),
                type="file_written",
                scope=Scope(),
                payload={"path": rel, "change_type": "added"},
            )


def _fixed_time() -> Any:
    from datetime import UTC, datetime

    return datetime(2020, 1, 1, tzinfo=UTC)
