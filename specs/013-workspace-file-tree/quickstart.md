# Quickstart: Workspace File Tree

See the files a run produced as a collapsible directory tree.

## Emit file events (SDK)

```python
from intui import run_recorder

with run_recorder("run.ndjson") as rec, rec.run():
    rec.file_written("README.md", change_type="added")
    rec.file_written("src/app.py", change_type="added")
    rec.file_written("src/util.py")
    rec.file_removed("src/old.py")
```

```sh
intui watch run.ndjson      # press `f` for the files view
```

You get a keyboard-navigable tree:

```
src
  app.py    (added)
  util.py   (modified)
README.md   (added)
```

## Inspect a real directory (no event stream)

```python
from intui.kit.state import scan_workspace
from intui.events import MemorySource
from intui.console import build_console

app = build_console(MemorySource(scan_workspace("./my_project")))
app.run()                   # press `f`
```

`scan_workspace` walks the directory and emits `file_written` events with paths
**relative** to the root (public-safe).

## Notes

- The tree is **public-safe by default** — relative workspace paths show
  normally; any absolute/host path is redacted.
- Directories are inferred from file paths; an empty directory isn't shown.
- This view is **read-only**. Acting on files (open/delete/download) is a later
  slice and will be an intent your app handles — the library never touches your
  disk on its own.
