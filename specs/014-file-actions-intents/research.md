# Research & Decisions: File Actions as Intents

**Feature**: `014-file-actions-intents` | **Date**: 2026-06-14

## D1 — Actions are intents; the library never mutates the FS

**Decision**: File actions are `Intent`s the application handles
(`open_file`, `copy_path`, `delete_file`); the library only posts them. No
filesystem mutation happens inside the library.

**Why**: Principle III (the application's handler is the sole mutation seam) and
VI (the tree may be fed by an untrusted stream — auto-deleting would be a footgun).
This is the line that keeps us a generic substrate rather than a file manager.

**Alternatives rejected**: have `FileTree`/`ConsoleApp` delete/open directly —
violates the boundary and makes a viewer dangerous.

## D2 — `delete_file` is `risky`; reuse the existing confirmation

**Decision**: `delete_file_intent(path)` sets `risky=True`, so `post_intent`
routes it through the built-in `ConfirmScreen` before delivery (open/copy are not
risky).

**Why**: Destructive actions must be confirmed (FR-016 from 001) and we already
have a keyboard-operable confirmation — no new UI. Delivery only on confirm.

**Alternatives rejected**: a bespoke delete dialog — duplicates the existing flow.

## D3 — Selection + dir/file via `Tree.cursor_node`

**Decision**: The action methods read `Tree.cursor_node`; a node is a **file**
when `allow_expand` is False (leaves are added via `add_leaf`), a **directory**
when True. `node.data` carries the path. Actions on a directory or when
`cursor_node` is None are no-ops.

**Why**: Uses Textual's own cursor (the visible selection) and the structure we
already build in 013 — no parallel selection state. Files-only matches scope.

**Alternatives rejected**: track selection separately — drift risk; allow dir
actions — out of scope and dangerous (recursive delete).

## D4 — Action keys o / c / x (avoid console view keys)

**Decision**: `FileTree.BINDINGS`: `o`=open, `c`=copy path, `x`=delete. They
apply when the tree (or its focused child) has focus and are shown in the footer.

**Why**: The console binds `t/l/f/d/e/p` app-globally; `o/c/x` don't collide, so
app navigation still works while the tree is focused, and the file actions are
context-scoped to the tree (standard TUI pattern). `x` for delete keeps the
destructive key distinct from anything navigational.

**Alternatives rejected**: `d` for delete — collides with the console's diff
view; `enter` — already used by `Tree` to select/expand.

## D5 — Opt-in convenience handlers in `intui.actions.files`

**Decision**: Ship `delete_path(path)`, `save_copy(src, dst)`, and
`open_in_editor(path, *, editor=None, run=None)` as engine-free helpers an app
calls from its handler. `open_in_editor` resolves `$EDITOR`→`$VISUAL`→a platform
opener (`os.startfile`/`open`/`xdg-open`); `run` is injectable for tests.

**Why**: The affordance is only useful if real behavior is a few lines away — but
those side effects must be the app's explicit choice, not the library's default.
Keeping them in `intui.actions` (engine-free) makes them reusable and testable
without a terminal; the injectable `run` avoids launching processes in CI.

**Alternatives rejected**: bake editor/delete into the widget — violates D1; a
clipboard helper here — Textual's `App.copy_to_clipboard` already covers copy at
the rendering layer.

## D6 — Console: copy real by default; open/delete opt-in via `file_actions`

**Decision**: `ConsoleApp.handle_intent` handles `copy_path` with
`self.copy_to_clipboard(path)` always. `open_file`/`delete_file` are fulfilled
with the helpers **only** when `build_console(file_actions=True)`; otherwise they
`notify` (report-only). The confirmation still gates delete regardless.

**Why**: A generic viewer should be safe out of the box (never delete unprompted)
yet make real actions one flag away. Copy is non-destructive and universally
handy, so it's on by default. This demonstrates the full pattern while honoring
"safe by default."

**Alternatives rejected**: real delete by default — unsafe for a viewer; no real
behavior at all — leaves the feature feeling hollow and the wiring undocumented.

## D7 — File-action intents are NOT events

**Decision**: `open_file`/`copy_path`/`delete_file` are application **intents**,
not stream events; they are not added to `KNOWN_EVENT_TYPES`.

**Why**: Intents are user requests flowing app-ward (Principle III); events are
append-only facts flowing into state. Mixing them would muddy the contract. (If
an app *wants* a deletion to reflect in the tree, it emits `file_removed` from its
handler — closing the loop through the normal event path.)

**Alternatives rejected**: model actions as events — wrong direction; conflates
request with fact.

## Open questions / deferred

- **Download/save key**: deferred — `save_copy` is provided for apps; a bound
  key + destination UX only matters with remote viewing (`textual serve`).
- **Directory actions** (bulk ops): out of scope (safety + UX).
- **"Reveal in file manager"**: could be another opt-in helper later.
