# Implementation Plan: Workspace File Tree

**Branch**: `013-workspace-file-tree` | **Date**: 2026-06-14 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/013-workspace-file-tree/spec.md`

## Summary

A generic, first-class filesystem tree fed by events:

1. **Engine-free state** (`intui.kit.state.workspace`): `WORKSPACE_EVENT_TYPES =
   {file_written, file_removed}`, a `WorkspaceState` (files keyed by normalized
   path + status), `workspace_slice()` reducer, and a `file_tree_view()` selector
   that projects the flat file set into a nested `FileNode` tree (dirs inferred,
   dirs-before-files, public-safe via the existing redactor). Unioned into
   `KNOWN_EVENT_TYPES`.
2. **Widget** (`intui.kit.file_tree`): a `FileTree` `BoundContainer` wrapping
   Textual's `Tree` (keyboard nav/focus free), rendering the nested model with
   dir/file glyphs + per-file status, refreshing from the snapshot.
3. **Producer SDK** (`intui.emit`): `file_written(path, *, change_type=…)` and
   `file_removed(path)` helpers.
4. **Live convenience** (`intui.kit.state.workspace.scan_workspace`): walk a real
   dir, yield `file_written` events with **relative** paths (a labeled IO helper).
5. **Integration**: a "files" view in the `ConsoleApp` (key `f`), so `intui watch`
   shows the tree; plus an example emitting file events.

Decisions in [research.md](research.md); shapes in [data-model.md](data-model.md);
surface in [contracts/contract-api.md](contracts/contract-api.md).

## Technical Context

**Language/Version**: Python 3.11–3.13 (unchanged).

**Primary Dependencies**: Textual 6.x (the widget uses its `Tree`). No new deps
(`scan_workspace` uses stdlib `os`/`pathlib`).

**Storage**: ndjson (unchanged).

**Testing**: pytest headless for the reducer (path nesting, status, removal +
pruning, separator normalization), the selector (nested structure, dirs-first,
redaction), the SDK helpers, and `scan_workspace` (relative paths from a temp
dir); Pilot for the `FileTree` widget + the console "files" view.

**Target Platform**: unchanged (Windows/macOS/Linux/WSL). Path normalization
(`\`→`/`) keeps the tree consistent cross-platform.

**Project Type**: library + examples gallery (unchanged).

**Performance Goals**: tree projection O(files); render coalescing unchanged.

**Constraints**: slice + selector + SDK + scan engine-free (layering guard);
public-safe by default (paths redacted); read-only (no mutations — actions are a
later intent-based slice); replayable (state-fed core deterministic).

**Scale/Scope**: one state module + one widget + 2 SDK helpers + a scan helper +
console "files" view + an example. Out of scope: file actions
(open/delete/download), process metrics, file contents (the diff view covers
changes), a live auto-refreshing FS watcher.

## Constitution Check

| # | Principle | Status | Notes |
|---|-----------|--------|-------|
| I | Structured State | ✅ PASS | The tree derives entirely from the `workspace` slice/snapshot. |
| II | Layered Architecture | ✅ PASS | State/selector/SDK/scan engine-free; only `FileTree` imports Textual. |
| III | Actions Are Intents | ✅ PASS | Read-only here; future file actions will be intents the app fulfills. |
| IV | Keyboard-First | ✅ PASS | Textual `Tree` gives nav + visible cursor; reachable by key in the console. |
| V | Meaningful Motion | ✅ PASS (n/a) | Static tree; status via glyph+label (non-color). |
| VI | Public-Safe | ✅ PASS | Paths redacted by default; `scan_workspace` emits relative paths. |
| VII | Test-First, Replayable | ✅ PASS | Reducer/selector/SDK/scan headless test-first; widget via Pilot. |
| VIII | Example-Driven | ✅ PASS | Example emits file events; console "files" view ships it (FR-011). |
| — | New deps justified | ✅ PASS | None. |

**Post-Phase-1 re-check (2026-06-14)**: no new deps; layering holds. GATE: PASS —
Complexity Tracking empty.

## Project Structure

```text
src/intui/kit/state/
├── workspace.py    # NEW — WORKSPACE_EVENT_TYPES, WorkspaceState, FileNode,
│                   #   workspace_slice(), file_tree_view(), scan_workspace()
└── __init__.py     # export workspace names; union into KNOWN_EVENT_TYPES

src/intui/kit/
├── file_tree.py    # NEW — FileTree(BoundContainer) over Textual Tree
└── __init__.py     # lazy-export FileTree

src/intui/emit.py   # + file_written(), file_removed()
src/intui/console/app.py  # + "files" view (FileTree) + key/command "f"

examples/emit_demo/run.py  # emit file_written for the files it diffs (shows the tree)

tests/
├── unit/
│   ├── test_workspace.py        # reducer + selector + scan_workspace
│   └── test_emit.py             # (extend) file_written/file_removed
├── snapshot/
│   └── test_file_tree.py        # Pilot: renders nested tree, keyboard nav
└── integration/
    └── test_console_app.py      # (extend) "files" view shows the tree
```

**Structure Decision**: the workspace model joins the other engine-free kit
slices; the `FileTree` is the only rendering-layer addition (wraps Textual
`Tree`); `scan_workspace` is a labeled IO convenience in the engine-free module
(stdlib only, clearly not part of the pure replayable path).

## Complexity Tracking

No constitutional violations — table intentionally empty.
