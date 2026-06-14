# API Contract: Workspace File Tree

**Feature**: `013-workspace-file-tree` | **Date**: 2026-06-14

New public surface and behavioral guarantees tests pin.

## Events

- `file_written` (payload `path`, optional `change_type`) and `file_removed`
  (payload `path`) are canonical types; `WORKSPACE_EVENT_TYPES ⊆
  KNOWN_EVENT_TYPES`.

## `intui.kit.state` — workspace model (engine-free)

```python
workspace_slice() -> tuple[Reducer, WorkspaceState]
file_tree_view(slice_name="workspace", *, public_safe=True) -> Selector[FileTreeView]
scan_workspace(root, *, run_id="workspace") -> Iterator[Event]
WorkspaceState, FileEntry, FileNode, FileTreeView, WORKSPACE_EVENT_TYPES
```

Guarantees:
- `file_written` upserts a normalized-path entry (status added/modified);
  `file_removed` removes it; unknown removals are ignored (no crash).
- `file_tree_view` nests paths into directories (inferred), **dirs before
  files**, alphabetical; empty dirs never appear; removal prunes now-empty dirs.
- Public-safe by default: displayed names/paths redacted (relative paths pass
  through; absolute/unsafe scrubbed). `public_safe=False` shows raw.
- Path separators normalized (`\`→`/`); the same logical file is one node.
- `scan_workspace(root)` yields `file_written` events with **relative** paths.

## `intui.kit` — widget (rendering layer)

```python
from intui.kit import FileTree
FileTree(file_tree_view(...), ...)   # BoundContainer over Textual Tree
```

Guarantees:
- Renders the nested tree from the snapshot; dirs vs files distinguished;
  per-file status shown; keyboard-navigable with visible cursor.
- Refreshes as events arrive; expansion preserved by node path across refreshes.

## `intui.emit` — SDK helpers

```python
rec.file_written(path, *, change_type="modified") -> Event
rec.file_removed(path) -> Event
```

Guarantees: valid canonical envelopes reducing into the tree as expected.

## `intui.console` — console integration

- `ConsoleApp` exposes a `files` view (a `FileTree`) reachable by key `f` and the
  command bar/palette; `build_console` wires a `workspace` slice. No app code
  needed for `intui watch` to show the tree.

## Backward compatibility

- Purely additive: new event types, a new slice/selector/widget, two SDK
  helpers, one console view. No existing signature changes. `KNOWN_EVENT_TYPES`
  grows (documented in the contract).
