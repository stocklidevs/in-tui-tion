# API Contract: File Actions as Intents

**Feature**: `014-file-actions-intents` | **Date**: 2026-06-14

New public surface and behavioral guarantees tests pin.

## Intent helpers (engine-free, `intui.kit.state`)

```python
open_file_intent(path) -> Intent      # name="open_file",   payload={"path"}
copy_path_intent(path) -> Intent      # name="copy_path",   payload={"path"}
delete_file_intent(path) -> Intent    # name="delete_file", payload={"path"}, risky=True
```

Guarantees:
- Carry the path; `delete_file` is `risky`.
- Posting performs **no** filesystem mutation (Principle III) — delivery to the
  app handler is the only effect.
- Not part of `KNOWN_EVENT_TYPES` (intents are requests, not events).

## `FileTree` actions (rendering layer)

Guarantees:
- Keys `o`/`c`/`x` post `open_file`/`copy_path`/`delete_file` for the
  **selected file**; `x` (delete) is gated by the built-in confirmation.
- Directory selection or no selection → no intent posted (no-op, no crash).
- Bindings are footer-discoverable and do not collide with the console view keys.
- `selected_file()` returns the selected file path or `None`.

## `intui.actions.files` (opt-in helpers, engine-free)

```python
from intui.actions.files import delete_path, save_copy, open_in_editor
delete_path(path) -> None
save_copy(src, dst) -> Path
open_in_editor(path, *, editor=None, run=None) -> list[str]
```

Guarantees:
- `delete_path` removes a file; `save_copy` copies and returns the dest;
  `open_in_editor` resolves the editor (`editor` → `$EDITOR` → `$VISUAL` →
  platform opener), invokes `run(argv)` (default `subprocess.Popen`), and returns
  the argv.
- Pure helpers an app calls; the library never invokes them on its own.
- Engine-free (no Textual import).

## Console integration

```python
build_console(..., file_actions=False) -> ConsoleApp
```

Guarantees:
- `copy_path` copies the path to the clipboard by default.
- `open_file`/`delete_file` are fulfilled (via the helpers) only when
  `file_actions=True`; otherwise reported (notify), never mutating.
- Delete remains gated by confirmation regardless of the flag.

## Backward compatibility

- Purely additive: intent helpers, FileTree bindings, a new `intui.actions.files`
  module, and a defaulted `file_actions=False` console flag. No existing
  signature changes; the contract event vocabulary is unchanged.
