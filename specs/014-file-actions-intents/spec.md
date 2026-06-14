# Feature Specification: File Actions as Intents

**Feature Branch**: `014-file-actions-intents`

**Created**: 2026-06-14

**Status**: Draft

**Input**: Follow-up to the workspace file tree (013). Users want to act on the
files a run produced — open, delete, copy/download. Per Principle III the library
must **never mutate the filesystem itself**: it surfaces actions as **intents**
the application fulfills, with the built-in confirmation for destructive ones.

## Overview

The `FileTree` (013) is read-only. This feature makes it **actionable** the
in-TUI-tion way: pressing a key on the selected file **posts an intent**
(`open_file`, `delete_file`, `copy_path`) which the application's handler decides
how to fulfill. Destructive intents (`delete_file`) are `risky` and flow through
the existing confirmation prompt before delivery. The library never touches disk.

To make this immediately useful without violating the boundary, we also ship:

- **Intent helpers** (`open_file_intent`, `delete_file_intent`, `copy_path_intent`)
  so any app/widget can request a file action.
- **Optional convenience handlers** (`intui.actions.files`: `open_in_editor`,
  `delete_path`, `save_copy`) — building blocks an app *chooses* to call from its
  handler. They are not auto-wired to destructive behavior.
- The zero-config `ConsoleApp` handles `copy_path` for real (clipboard) by
  default and treats `open_file`/`delete_file` as **opt-in** via
  `build_console(file_actions=True)`; with the flag off (default) it only
  notifies — a generic viewer never deletes your files unprompted.

This keeps us a substrate: we provide the affordance, the confirmation, and the
reusable handlers; the application owns the side effect.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Act on a file via intents (Priority: P1)

A user selects a file in the tree and presses a key; the app receives a
corresponding intent carrying the file path and decides what to do.

**Why this priority**: Turning the read-only tree into an actionable surface is
the whole feature, and doing it as intents is what keeps the library generic.

**Independent Test**: Mount a `FileTree` in an app with a recording handler;
select a file, press the action keys; assert the expected intents (with the path)
are delivered; directories yield no file action.

**Acceptance Scenarios**:

1. **Given** a selected file, **When** the user presses the open key, **Then**
   an `open_file` intent with that path is delivered to the app's handler.
2. **Given** a selected file, **When** the user presses the copy key, **Then** a
   `copy_path` intent with that path is delivered.
3. **Given** a selected **directory** (or no selection), **When** an action key
   is pressed, **Then** no file-action intent is posted.

---

### User Story 2 - Delete is confirmed and never performed by the library (Priority: P1)

Pressing delete on a file raises the built-in confirmation; only on confirm is a
`delete_file` intent delivered — and the library itself never removes the file.

**Why this priority**: Destructive actions must be safe-by-default and clearly
the application's responsibility (Principle III + VI).

**Independent Test**: Press the delete key on a file; assert the confirmation
prompt appears; confirm → a `delete_file` intent is delivered; cancel → nothing
is delivered; in neither case does the library touch the filesystem.

**Acceptance Scenarios**:

1. **Given** a selected file, **When** the user presses delete, **Then** the
   confirmation prompt appears and no intent is delivered yet.
2. **Given** the prompt, **When** the user confirms, **Then** a `delete_file`
   (`risky`) intent with the path is delivered.
3. **Given** the prompt, **When** the user cancels, **Then** no intent is
   delivered.
4. **Given** any path, **When** these intents are posted, **Then** the library
   performs no filesystem mutation on its own.

---

### User Story 3 - Wire real behavior with the provided helpers (Priority: P2)

An app turns the intents into real actions using `intui.actions.files`, or
enables the console's built-in opt-in handlers.

**Why this priority**: The affordance is only valuable if real behavior is easy
to wire — but it must be opt-in, not default.

**Independent Test**: Call `delete_path` / `save_copy` on temp files and assert
the effect; call `open_in_editor` with an injected runner and assert the argv;
build the console with `file_actions=True` and assert delete/open are fulfilled,
and with it off assert they are not.

**Acceptance Scenarios**:

1. **Given** `intui.actions.files.delete_path(p)`, **When** called, **Then** the
   file is removed; `save_copy(src, dst)` copies; `open_in_editor` runs the
   resolved editor with the path (via an injectable runner).
2. **Given** `build_console(file_actions=True)`, **When** a `delete_file` intent
   is confirmed, **Then** the file is removed; **Given** the default
   (`file_actions=False`), **Then** it is only reported, not removed.
3. **Given** the default console, **When** `copy_path` fires, **Then** the path
   is copied to the clipboard.

---

### Edge Cases

- Action key pressed with nothing selected: no intent, no crash.
- Action on a directory node: no file action (this feature targets files).
- Delete confirmation cancelled: no delivery, no mutation.
- `open_in_editor` with no `$EDITOR`/`$VISUAL`: falls back to the platform opener;
  resolution is testable via an injected runner.
- `delete_path` on a missing file / `save_copy` to a bad dest: the helper raises
  (the app handles it); the library core never crashes from an intent.
- The console with `file_actions=False` must never mutate the filesystem.

## Requirements *(mandatory)*

### Functional Requirements

**Intents (engine-free)**

- **FR-001**: Provide `open_file_intent(path)`, `copy_path_intent(path)`, and
  `delete_file_intent(path)` (the last with `risky=True`) building `Intent`s
  carrying the path.
- **FR-002**: The library MUST NOT perform any filesystem mutation when these
  intents are posted; delivery to the application handler is the only effect
  (Principle III).

**FileTree affordances**

- **FR-003**: `FileTree` MUST bind action keys that, for the currently-selected
  **file**, post the matching intent via the app (`post_intent`), inheriting the
  risky-action confirmation for delete.
- **FR-004**: Action keys on a directory or with no selection MUST be no-ops.
- **FR-005**: The action keys/labels MUST be discoverable (widget bindings shown
  in the footer) and not collide with the console's view keys.

**Convenience handlers (opt-in side effects)**

- **FR-006**: Provide `intui.actions.files` helpers: `delete_path(path)`,
  `save_copy(src, dst)`, and `open_in_editor(path, *, editor=None, run=None)`
  (resolves `$EDITOR`/`$VISUAL` then a platform opener; `run` injectable). These
  are conveniences an app calls; they are not invoked by the library on its own.

**Console integration**

- **FR-007**: `ConsoleApp` MUST handle `copy_path` for real (copy to clipboard)
  by default.
- **FR-008**: `ConsoleApp` MUST treat `open_file`/`delete_file` as **opt-in** via
  `build_console(file_actions=True)`: enabled → fulfilled with the helpers;
  default (off) → reported only (no mutation).

**Cross-cutting**

- **FR-009**: Intent helpers + `intui.actions.files` MUST be engine-free
  (layering guard) and headlessly testable; `FileTree` actions via Pilot.

### Key Entities

- **File-action intents**: `open_file`, `copy_path`, `delete_file` (risky), each
  carrying `path`.
- **`intui.actions.files`**: opt-in helper functions (`delete_path`, `save_copy`,
  `open_in_editor`) the app uses to fulfill intents.
- **`file_actions` flag**: the console's opt-in switch for real open/delete.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Action keys on a selected file deliver the matching intent with the
  path; dirs/no-selection deliver nothing (verified via Pilot).
- **SC-002**: `delete_file` is gated by the confirmation prompt; confirm delivers,
  cancel does not; the library never deletes the file itself (verified).
- **SC-003**: `intui.actions.files` helpers perform their effect on temp files /
  resolve the editor argv (verified headlessly).
- **SC-004**: `build_console(file_actions=True)` fulfills delete/open; default
  does not mutate; `copy_path` copies to the clipboard (verified).
- **SC-005**: All intent helpers + action helpers are engine-free (layering
  guard green).

## Assumptions

- The tree targets **files**; acting on directories (bulk delete, etc.) is out of
  scope here.
- "Download" is deferred — for a local console it is ~`save_copy`, and it only
  becomes meaningful with remote viewing; `save_copy` is provided for apps but no
  `download` key is bound yet.
- File-action *intents* are application requests, not stream events — they are not
  added to the canonical event vocabulary.
- The convenience handlers are best-effort OS helpers (editor/platform-open vary
  by environment); they are opt-in and the app owns error handling.
- Public-safety: the tree still redacts paths on display (013); intents carry the
  real selected path to the app (which already trusts its own workspace).
