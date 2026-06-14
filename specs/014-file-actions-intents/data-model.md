# Data Model: File Actions as Intents

**Feature**: `014-file-actions-intents` | **Date**: 2026-06-14

No new events or snapshot shapes — file actions are **intents** (application
requests), plus opt-in helper functions. This documents the new surface.

## File-action intents (engine-free, `intui.kit.state.workspace`)

```text
open_file_intent(path: str)   -> Intent("open_file",   {"path": path})
copy_path_intent(path: str)   -> Intent("copy_path",   {"path": path})
delete_file_intent(path: str) -> Intent("delete_file", {"path": path}, risky=True)
```

- All carry `{"path": <selected file path>}`.
- `delete_file` is `risky` → held by the confirmation flow until the user
  confirms (existing 001 behavior).
- Posting an intent performs **no** filesystem mutation; the app's handler is the
  only effect. These are NOT added to `KNOWN_EVENT_TYPES` (intents ≠ events).

## `FileTree` actions (rendering layer)

`FileTree.BINDINGS`:

| key | action | intent | gating |
|---|---|---|---|
| `o` | open | `open_file_intent(path)` | file only |
| `c` | copy path | `copy_path_intent(path)` | file only |
| `x` | delete | `delete_file_intent(path)` | file only; risky → confirm |

Action methods read `Tree.cursor_node`; act only when it is a **file**
(`allow_expand` False) with a `data` path, posting via `self.app.post_intent`.
Directory / no-selection → no-op. Introspection: `selected_file() -> str | None`.

## `intui.actions.files` (opt-in side-effect helpers, engine-free)

```text
delete_path(path: Path | str) -> None
    # remove a file (Path.unlink); raises if missing — caller handles.

save_copy(src: Path | str, dst: Path | str) -> Path
    # shutil.copy(src, dst); returns the destination path.

open_in_editor(path: Path | str, *, editor: str | None = None,
               run: Callable[[list[str]], Any] | None = None) -> list[str]
    # resolve editor: explicit -> $EDITOR -> $VISUAL -> platform opener
    #   (os.startfile via "cmd /c start" argv on Windows, "open" on macOS,
    #    "xdg-open" on Linux); invoke `run(argv)` (default subprocess.Popen);
    #   return the argv (for tests / logging).
```

These are conveniences an app calls from its handler; the library never invokes
them itself. `run` is injectable so tests assert argv without launching anything.

## Console integration (`intui.console`)

```text
build_console(source, *, public_safe=True, sweep_seconds=1.6, file_actions=False) -> ConsoleApp
```

`ConsoleApp.handle_intent` adds:
- `copy_path` → `self.copy_to_clipboard(path)` + notify (always).
- `open_file` → `file_actions` ? `open_in_editor(path)` : notify (report-only).
- `delete_file` → `file_actions` ? `delete_path(path)` + notify : notify
  (report-only). (Confirmation already gated delivery.)

Default `file_actions=False`: the viewer never mutates the filesystem.

## What does NOT change

- Event envelope/vocabulary, store, snapshots, the workspace slice + tree
  view-model, all other widgets. Additive: 3 intent helpers, FileTree bindings,
  `intui.actions.files`, a console flag + handler branches.
