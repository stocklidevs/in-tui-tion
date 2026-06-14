# Quickstart: File Actions as Intents

Act on the files in the tree — the library posts **intents**, your app decides.

## In the console

Press in the **files** view (`f`) on a selected file:

- `o` — open · `c` — copy path · `x` — delete (asks to confirm)

By default the console copies paths to the clipboard and *reports* open/delete
(it never touches your disk). Turn on real actions explicitly:

```python
from intui.console import build_console
app = build_console(source, file_actions=True)   # open in $EDITOR, real delete
app.run()
```

## Handle the intents in your own app

```python
from intui.app import IntuiApp
from intui.actions.files import open_in_editor, delete_path, save_copy

class MyApp(IntuiApp):
    async def handle_intent(self, intent):
        path = intent.payload.get("path")
        if intent.name == "open_file":
            open_in_editor(path)                 # $EDITOR / $VISUAL / platform opener
        elif intent.name == "delete_file":       # already confirmed (risky)
            delete_path(path)
            self._emit("file_removed", path=path)  # reflect it back in the tree
        elif intent.name == "copy_path":
            self.copy_to_clipboard(path)
```

## Request an action from code

```python
from intui.kit.state import open_file_intent, delete_file_intent, copy_path_intent

app.post_intent(delete_file_intent("src/old.py"))  # risky -> confirmation first
```

## The boundary

The library **never mutates the filesystem**. It surfaces the affordance (keys +
confirmation), posts intents, and ships opt-in helpers — your application performs
the side effect (Principle III). Deletions are `risky`, so they always go through
the confirmation prompt before your handler is called.
