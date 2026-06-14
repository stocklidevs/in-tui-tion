# Implementation Plan: File Actions as Intents

**Branch**: `014-file-actions-intents` | **Date**: 2026-06-14 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/014-file-actions-intents/spec.md`

## Summary

Make the `FileTree` (013) actionable without the library ever touching disk:

1. **Intent helpers** (engine-free, `intui.kit.state.workspace`):
   `open_file_intent(path)`, `copy_path_intent(path)`, and
   `delete_file_intent(path)` (`risky=True`).
2. **`FileTree` action keys** (`o` open, `c` copy, `x` delete): on the
   currently-selected **file** (`Tree.cursor_node`, leaf = `allow_expand` False),
   post the matching intent via `self.app.post_intent` — delete inherits the
   built-in confirmation. Dirs / no selection = no-op. Bindings shown in the
   footer; keys chosen to avoid the console's view keys (t/l/f/d/e/p).
3. **Opt-in convenience handlers** (engine-free, `intui.actions.files`):
   `delete_path(path)`, `save_copy(src, dst)`, `open_in_editor(path, *,
   editor=None, run=None)` (resolve `$EDITOR`/`$VISUAL` → platform opener; `run`
   injectable). The library never calls these on its own.
4. **Console integration**: `ConsoleApp` handles `copy_path` for real
   (`self.copy_to_clipboard`) by default; `open_file`/`delete_file` are **opt-in**
   via `build_console(file_actions=True)` — enabled fulfils with the helpers,
   default reports only (no mutation).

Decisions in [research.md](research.md); shapes in [data-model.md](data-model.md);
surface in [contracts/contract-api.md](contracts/contract-api.md).

## Technical Context

**Language/Version**: Python 3.11–3.13 (unchanged).

**Primary Dependencies**: Textual 6.x (the `FileTree` widget + `App.copy_to_
clipboard`). No new deps (`intui.actions.files` uses stdlib `os`/`shutil`/
`subprocess`/`pathlib`).

**Storage**: n/a (intents are app requests, not events).

**Testing**: pytest headless for the intent helpers + `intui.actions.files`
(temp files; injected runner for the editor); Pilot for `FileTree` posting
intents (recording handler), the delete confirmation flow, and the console
`file_actions` on/off behavior.

**Target Platform**: unchanged. `open_in_editor` resolves a cross-platform opener
(`os.startfile` / `open` / `xdg-open`); tested via an injected runner so no real
process launches in CI.

**Project Type**: library + examples gallery (unchanged).

**Performance Goals**: n/a (event-free affordance).

**Constraints**: Principle III — the library performs **no** filesystem mutation;
intents are the only effect. Helpers are opt-in and engine-free (layering guard).
Action keys must not collide with console view keys; destructive intent is risky.

**Scale/Scope**: 3 intent helpers + FileTree bindings + `intui.actions.files`
(3 helpers) + console `file_actions` flag/handlers + example/docs. Out of scope:
directory actions, a bound "download" key (remote concern; `save_copy` provided),
adding intents to the event vocabulary.

## Constitution Check

| # | Principle | Status | Notes |
|---|-----------|--------|-------|
| I | Structured State | ✅ PASS (n/a) | No new state; the tree still derives from the workspace slice. |
| II | Layered Architecture | ✅ PASS | Intent helpers + `intui.actions.files` engine-free; only `FileTree`/`ConsoleApp` touch Textual. |
| III | Actions Are Intents | ✅ PASS (core of the feature) | The library posts intents and never mutates the FS; the app fulfills. |
| IV | Keyboard-First | ✅ PASS | Action keys with footer-visible bindings; confirmation is keyboard-operable. |
| V | Meaningful Motion | ✅ PASS (n/a) | — |
| VI | Public-Safe | ✅ PASS | Tree still redacts on display; mutation is opt-in; viewer never deletes by default. |
| VII | Test-First, Replayable | ✅ PASS | Helpers + intents headless test-first; FileTree/console via Pilot. |
| VIII | Example-Driven | ✅ PASS | emit_demo/console doc shows the actions; opt-in wiring documented. |
| — | New deps justified | ✅ PASS | None. |

**Post-Phase-1 re-check (2026-06-14)**: no new deps; layering holds. GATE: PASS —
Complexity Tracking empty.

## Project Structure

```text
src/intui/kit/state/workspace.py   # + open_file_intent / copy_path_intent / delete_file_intent
src/intui/kit/file_tree.py         # + BINDINGS (o/c/x) + action methods (selected file -> post_intent)
src/intui/actions/files.py         # NEW — delete_path, save_copy, open_in_editor (opt-in helpers)
src/intui/actions/__init__.py      # export the file helpers
src/intui/console/app.py           # ConsoleApp file_actions flag + handle_intent branches

examples/emit_demo/README.md       # note the file-action keys (o/c/x) in the files view

tests/
├── unit/
│   ├── test_workspace.py          # (extend) intent helpers shape (+ risky delete)
│   └── test_file_actions.py       # intui.actions.files: delete_path/save_copy/open_in_editor
├── snapshot/
│   └── test_file_tree.py          # (extend) action keys post intents; dir/no-sel no-op
└── integration/
    └── test_console_app.py        # (extend) copy real; delete confirm; file_actions on/off
```

**Structure Decision**: intents live with the workspace model (engine-free,
beside `select_view_intent`); the opt-in side-effect helpers get their own
engine-free `intui.actions.files`; the only rendering-layer edits are `FileTree`
bindings and the `ConsoleApp` handler. The library's mutation surface stays zero.

## Complexity Tracking

No constitutional violations — table intentionally empty.
