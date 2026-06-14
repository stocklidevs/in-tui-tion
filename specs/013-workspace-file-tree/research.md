# Research & Decisions: Workspace File Tree

**Feature**: `013-workspace-file-tree` | **Date**: 2026-06-14

## D1 — Directories are inferred from file paths (no directory events)

**Decision**: The vocabulary is `file_written` / `file_removed` only. Directories
are derived by splitting a file's path on `/`; a directory with no files does not
appear.

**Why**: Files are the facts a run produces; modeling directories separately adds
a second event type and the empty-dir edge case for little value. Inferring keeps
the producer side trivial (`rec.file_written("src/app.py")` is enough) and the
tree always reflects real content.

**Alternatives rejected**: explicit `dir_added`/`dir_removed` — more vocabulary,
empty-dir bookkeeping, and producers rarely care about empty dirs.

## D2 — Flat file map in state; nest in the selector

**Decision**: `WorkspaceState.files` is a flat `Mapping[path, FileEntry(status)]`.
The `file_tree_view()` selector builds the nested `FileNode` tree on projection.

**Why**: A flat map makes the reducer trivial and idempotent (write = upsert,
remove = pop), and keeps state minimal/serializable. Nesting is a *view* concern,
memoized per snapshot like every other selector. Removal auto-prunes empty dirs
because the tree is rebuilt from whatever files remain.

**Alternatives rejected**: store a nested tree in state — harder to update,
duplicates structure the selector can derive, and complicates removal/pruning.

## D3 — Path normalization + relative paths

**Decision**: Normalize separators (`\`→`/`) and strip leading `./`/`/` when
keying. `scan_workspace(root)` emits paths **relative** to `root`.

**Why**: Consistent keys across OSes so the same logical file isn't duplicated;
relative paths keep the tree public-safe (no host prefix) and portable. The 011
redactor already lets relative paths through and redacts absolute ones, so an
accidental absolute path is still scrubbed by default.

**Alternatives rejected**: keep raw paths — duplicate nodes for `\` vs `/`, and
absolute host paths leaking into the view.

## D4 — Per-file status: added / modified (removal deletes)

**Decision**: `file_written` carries an optional `change_type`; the entry status
is `added` (first sight or `change_type="added"`) or `modified`. `file_removed`
deletes the entry (no tombstone).

**Why**: "What's in the workspace now, and what just changed" is the useful
signal; a removed file should disappear from a *current-state* tree. Status gives
the widget a glyph/color for recently-touched files without a full history model.

**Alternatives rejected**: keep removed files as tombstones — clutters a
"current workspace" view; a full per-file history — out of scope (the diff view
already shows content changes).

## D5 — Widget wraps Textual `Tree` (not `DirectoryTree`)

**Decision**: `FileTree` wraps Textual's generic `Tree`, building nodes
recursively from the `FileNode` model. We do **not** use Textual's
`DirectoryTree` (which walks the live filesystem).

**Why**: `DirectoryTree` is live-FS and breaks our state-derived, replayable
model (Principle I) and public-safety. The generic `Tree` gives keyboard nav,
visible cursor, expand/collapse, and scrolling for free while we keep the data
direction (view-model in → nodes out), exactly like `TaskTree`.

**Alternatives rejected**: `DirectoryTree` — couples the widget to the real FS;
a hand-rolled tree — re-implements nav/cursor Textual already provides.

## D6 — `scan_workspace` is a labeled IO convenience, engine-free but impure

**Decision**: `scan_workspace(root)` lives in the engine-free `workspace` module,
uses stdlib `os.walk`/`pathlib`, and yields `file_written` `Event`s with relative
paths. It is documented as a side-effecting convenience, separate from the pure,
replayable core.

**Why**: It needs no terminal engine (so it stays engine-free and the layering
guard passes), but it reads the live FS so it isn't deterministic — clearly
flagged, like `SubprocessSource`/`JsonlReplaySource` on the consume side. Lets
users get a tree from a directory with one call when there's no event stream.

**Alternatives rejected**: a Textual `DirectoryTree`-based widget (D5); a
background FS watcher — bigger scope, deferred.

## D7 — Read-only now; actions are a later intent-based slice

**Decision**: This feature renders the tree only. Open/delete/download are **not**
included; when added they will be `Intent`s the application fulfills (with the
existing risky-action confirmation), never mutations the library performs.

**Why**: Keeps us a generic substrate (a tree primitive), honors Principle III,
and avoids security pitfalls of acting on a tree fed by an untrusted stream
(Principle VI). Ships the high-value inspection capability now; actions later.

**Alternatives rejected**: bundle delete/open now — turns the library into a file
manager and violates the "library never mutates" boundary.

## D8 — Console integration: a "files" view

**Decision**: Add a `files` view (a `FileTree`) to `ConsoleApp`'s router, keyed
`f`, alongside tasks/lanes/diff/evidence.

**Why**: Makes the tree real and zero-config — `intui watch` a stream with
`file_*` events and press `f`. Reuses the existing view-router + command-bar
machinery (007/009).

**Alternatives rejected**: leave it widget-only — misses the "no code" payoff and
the obvious place users look.

## Open questions / deferred

- **File actions** (open/delete/download as intents) — the next slice.
- **Process metrics** ("run it and watch resources") — separate feature.
- **Live FS auto-refresh** (watchdog) — `scan_workspace` is one-shot; a watcher
  is deferred.
- **IntentForge tree for free**: IF `file_diff` carries `file`; a later adapter
  tweak could also surface those as `file_written` so an IF run shows a tree —
  noted, not in this feature (adapter `adapt_record` is 1:1 today).
