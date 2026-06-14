# Feature Specification: Workspace File Tree

**Feature Branch**: `013-workspace-file-tree`

**Created**: 2026-06-14

**Status**: Draft

**Input**: User request — a run (e.g. IntentForge) creates code in a workspace;
we want to **inspect the directory tree** of what it produced. Framed as a
first-class generic TUI primitive (a filesystem tree fed by events), not an
IF-specific file manager. File *actions* (open/delete/download) and process
metrics are separate, later slices.

## Overview

in-TUI-tion has no generic hierarchical file view — only `TaskTree`
(tree-over-taskboard). This feature adds a **workspace file tree**: a `file_*`
event vocabulary reduced into a `workspace` slice, a nested tree view-model, and
a keyboard-navigable `FileTree` widget — so a run's produced files appear as a
collapsible directory tree, **public-safe and replayable**.

Two ways to feed it, by design:

- **State-fed (the core / in-TUI-tion way)**: a producer emits `file_written` /
  `file_removed` events; we reduce them into the workspace tree. This stays pure
  and replayable — scrub a recording and watch the tree grow as files are
  written. Pairs with the emit SDK (`rec.file_written("src/app.py")`).
- **Live convenience**: `scan_workspace(root)` walks a real directory and yields
  `file_written` events (relative paths), for the no-event-stream case — a
  clearly-separated IO helper, like the runner's subprocess source.

The tree is **read-only** here: it renders structure and per-file status. Acting
on files (open/delete/download) is the next slice and will be **intents the app
fulfills**, never mutations the library performs (Principle III). The zero-config
console gains a "files" view so `intui watch` shows the tree with no code.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - See the produced files as a tree (Priority: P1)

A run emits `file_written` events as it creates/edits files. The console shows a
collapsible directory tree of the workspace, with directories and files
distinguished and recently-changed files marked.

**Why this priority**: Inspecting *what a run produced* is the core ask, and a
generic tree is a primitive the library is missing.

**Independent Test**: Reduce a set of `file_written` events headlessly; assert
the tree view-model nests paths correctly (dirs contain files), tracks status,
and is public-safe; render it via Pilot and navigate by keyboard.

**Acceptance Scenarios**:

1. **Given** `file_written` events for `src/app.py`, `src/util.py`, `README.md`,
   **When** reduced, **Then** the tree has a `src` directory containing `app.py`
   and `util.py`, plus a top-level `README.md`.
2. **Given** a `file_removed` for a path, **When** reduced, **Then** that file no
   longer appears (and empty parent dirs collapse away).
3. **Given** the tree renders, **When** the user navigates with the keyboard,
   **Then** nodes expand/collapse and focus is visible.
4. **Given** public-safe is on (default), **When** rendered, **Then** any unsafe
   absolute path/segment is redacted; relative workspace paths show normally.

---

### User Story 2 - Emit file events from a tool (Priority: P1)

A developer using the Producer SDK records the files their tool writes, so the
tree appears with no JSON by hand.

**Why this priority**: The state-fed path is only as good as how easy it is to
produce the events; the SDK must cover it.

**Independent Test**: Use `rec.file_written(...)` / `rec.file_removed(...)`;
assert valid envelopes that reduce into the expected tree.

**Acceptance Scenarios**:

1. **Given** `rec.file_written("src/app.py", change_type="added")`, **When**
   emitted, **Then** it is a valid canonical envelope reducing into the tree as
   an added file.
2. **Given** `rec.file_removed("src/old.py")`, **When** emitted and reduced,
   **Then** the file is removed from the tree.

---

### User Story 3 - Inspect a real directory live (Priority: P2)

A developer points the tree at an existing directory (no event stream) and sees
its structure.

**Why this priority**: A useful fallback when the producer doesn't emit file
events; convenience, not the core model.

**Independent Test**: `scan_workspace(tmp_dir)` over a small tree yields
`file_written` events with **relative** paths that reduce into the expected tree.

**Acceptance Scenarios**:

1. **Given** a directory with nested files, **When** `scan_workspace(root)` runs,
   **Then** it yields `file_written` events with paths relative to `root`.
2. **Given** those events fed through a store, **When** rendered, **Then** the
   tree mirrors the directory.

---

### Edge Cases

- Deeply nested paths and many files: the tree nests correctly and stays
  responsive (existing render coalescing).
- A `file_written` for a path already present: updates its status in place (no
  duplicate node).
- A `file_removed` for an unknown path: ignored (no crash).
- Mixed path separators (`\` vs `/`): normalized so the tree is consistent.
- An empty workspace (no file events): the tree shows an empty state.
- A path that is just a filename (no directory): appears at the top level.
- Absolute or unsafe paths in events: redacted by default (Principle VI), so the
  tree never leaks a host path.

## Requirements *(mandatory)*

### Functional Requirements

**State + view-model (engine-free)**

- **FR-001**: The system MUST provide a `workspace` slice that reduces
  `file_written` and `file_removed` events into a set of files keyed by
  normalized path, tracking a per-file status (added / modified).
- **FR-002**: The system MUST provide a tree view-model/selector that projects
  the flat file set into a nested directory tree (directories inferred from path
  segments; dirs before files; stable alpha order).
- **FR-003**: `file_removed` MUST remove the file; directories with no remaining
  descendants MUST NOT appear.
- **FR-004**: The view-model MUST be public-safe by default (paths redacted via
  the existing redactor), with the same opt-out parameter as other views.
- **FR-005**: `file_written`/`file_removed` MUST be added to the canonical
  vocabulary (`WORKSPACE_EVENT_TYPES` unioned into `KNOWN_EVENT_TYPES`).

**Widget (rendering layer)**

- **FR-006**: The system MUST provide a `FileTree` bound widget that renders the
  tree, distinguishes directories from files, shows per-file status, and is
  keyboard-navigable with visible focus (Principle IV).
- **FR-007**: The `FileTree` MUST derive entirely from the snapshot (Principle I)
  and refresh as events arrive.

**Producer SDK + live convenience**

- **FR-008**: The Producer SDK MUST provide `file_written(path, *,
  change_type="modified")` and `file_removed(path)` helpers emitting the
  canonical events.
- **FR-009**: The system MUST provide `scan_workspace(root)` that walks a real
  directory and yields `file_written` events with **relative** paths (a
  side-effecting convenience, separate from the pure core).

**Integration**

- **FR-010**: The zero-config `ConsoleApp` MUST expose a "files" view (a
  `FileTree`) reachable by a key/command, so `intui watch` shows the workspace
  with no application code.
- **FR-011**: A runnable example MUST demonstrate the tree end-to-end (a producer
  emitting file events, watchable).

**Cross-cutting**

- **FR-012**: The slice + selector + SDK helpers + `scan_workspace` MUST be
  engine-free (layering guard) and headlessly testable; the widget via Pilot.

### Key Entities

- **WorkspaceState**: files keyed by normalized path, each with a status.
- **FileNode (tree view-model)**: name, path, is_dir, status, children.
- **FileTree (widget)**: the bound, keyboard-navigable directory tree.
- **`file_written` / `file_removed`**: the canonical workspace event vocabulary.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A set of `file_written` events renders as a correct nested tree
  (dirs contain their files), verified headlessly + via Pilot.
- **SC-002**: `file_removed` removes a file and prunes now-empty directories.
- **SC-003**: The tree is public-safe by default (no host paths leak); relative
  workspace paths render normally.
- **SC-004**: `rec.file_written/removed` produce valid envelopes that build the
  expected tree; `scan_workspace` reproduces a real directory as relative-path
  events.
- **SC-005**: `intui watch` shows the workspace tree via the console "files"
  view with zero application code.
- **SC-006**: The tree is fully keyboard-navigable.

## Assumptions

- Directories are **inferred** from file paths — there is no separate directory
  event (a written file implies its parent dirs; a dir with no files isn't shown).
- The tree is **read-only** in this feature; file actions (open/delete/download)
  are a later slice and will be intents the app fulfills, not library mutations.
- Process/resource metrics ("run the code and watch it") is a separate later
  feature; this one is workspace inspection only.
- `scan_workspace` emits relative paths to keep the tree public-safe and portable;
  it is a convenience and not part of the replayable pure core.
- File *contents* are out of scope here (the diff view already shows changes);
  this is structure + status only.
