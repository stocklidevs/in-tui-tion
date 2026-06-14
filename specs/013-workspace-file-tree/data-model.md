# Data Model: Workspace File Tree

**Feature**: `013-workspace-file-tree` | **Date**: 2026-06-14

New canonical event types `file_written` / `file_removed`, a `workspace` slice,
a nested tree view-model, and the `FileTree` widget.

## Events (canonical vocabulary additions)

| `type` | scope | payload | meaning |
|---|---|---|---|
| `file_written` | — | `path` (required), `change_type?` (`added`/`modified`) | a file was created/edited |
| `file_removed` | — | `path` (required) | a file was deleted |

`WORKSPACE_EVENT_TYPES = frozenset({"file_written", "file_removed"})`, unioned
into `KNOWN_EVENT_TYPES`.

## `workspace` slice (engine-free)

```text
FileEntry(path: str, status: str)          # status: "added" | "modified"
WorkspaceState(files: Mapping[str, FileEntry])   # keyed by normalized path
workspace_slice() -> (reducer, WorkspaceState())
```

Reducer:
- `file_written`: normalize `path` (`\`→`/`, strip `./`/leading `/`); upsert
  `FileEntry(path, status)` where status = `change_type` if given else `added`
  for a new path / `modified` for an existing one. Ignored if `path` missing.
- `file_removed`: pop the normalized path (ignored if absent).

## Tree view-model + selector

```text
FileNode(
    name: str,           # the path segment (leaf or dir name)
    path: str,           # full normalized path to this node
    is_dir: bool,
    status: str,         # files: added/modified; dirs: "" 
    glyph: str,          # non-color identity (dir vs file vs status)
    children: tuple[FileNode, ...] = (),
)
FileTreeView(roots: tuple[FileNode, ...] = ())

file_tree_view(slice_name="workspace", *, public_safe=True) -> Selector[FileTreeView]
```

Projection:
- Build a nested structure by splitting each file path on `/`.
- Directories are inferred (interior segments); a dir node's `children` are its
  entries; **dirs sorted before files**, then alphabetical.
- Each displayed `name`/`path` is redacted when `public_safe` (default true) via
  the existing `redact` (relative paths pass through; absolute/unsafe scrubbed).
- Empty directories cannot occur (only paths with files create nodes).

## `scan_workspace` (live convenience)

```text
scan_workspace(root: Path | str, *, run_id: str = "workspace") -> Iterator[Event]
```

Walks `root` with stdlib `os.walk`; yields a `file_written` `Event` per file with
`path` **relative** to `root` (normalized, `change_type="added"`). Side-effecting
(reads the FS) and one-shot; feed via `MemorySource(scan_workspace(root))`.

## `FileTree` widget (rendering layer)

`FileTree(BoundContainer)` wraps Textual `Tree[str]`:
- `sync_view(FileTreeView)`: rebuild nodes recursively from `roots`; dir nodes
  expandable (expanded by default), file nodes are leaves; label =
  `glyph + name` (+ status for files). Preserves expansion by node path across
  refreshes. Keyboard nav/cursor/scroll come from `Tree`.
- Introspection helpers for tests (`paths()`, `labels()`).

## Console integration

`ConsoleApp` gains a `files` view (`FileTree(file_tree_view(public_safe=…))`) in
its `ViewRouter`, a command `Command("view_files","Files",select_view_intent
("files"),key="f")`, and `"files"` in `VIEWS` + the store's `workspace` slice.

## Producer SDK

```text
RunRecorder.file_written(path: str, *, change_type: str = "modified") -> Event
RunRecorder.file_removed(path: str) -> Event
```

Thin wrappers over `emit("file_written"/"file_removed", path=…, …)`.

## What does NOT change

- Envelope, store, health, snapshots, existing slices/widgets, the diff/evidence
  views. Additive: new event types, a new slice, a new widget, two SDK helpers,
  one console view.
