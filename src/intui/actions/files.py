"""Opt-in file-action helpers an application calls to fulfill file intents.

These are conveniences — the library NEVER calls them on its own (Principle III).
An app wires them from its ``handle_intent`` (or enables them in the console via
``build_console(file_actions=True)``). Engine-free (stdlib only); ``open_in_editor``
takes an injectable ``run`` so callers/tests can avoid launching a process.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

Runner = Callable[[list[str]], Any]


def delete_path(path: Path | str) -> None:
    """Delete a file. Raises ``FileNotFoundError`` if it is absent."""
    Path(path).unlink()


def save_copy(src: Path | str, dst: Path | str) -> Path:
    """Copy ``src`` to ``dst`` and return the destination path."""
    shutil.copy(src, dst)
    return Path(dst)


def open_in_editor(
    path: Path | str,
    *,
    editor: str | None = None,
    run: Runner | None = None,
) -> list[str]:
    """Open ``path`` in an editor and return the argv that was invoked.

    Resolution order: ``editor`` → ``$EDITOR`` → ``$VISUAL`` → a platform opener
    (``cmd /c start`` on Windows, ``open`` on macOS, ``xdg-open`` elsewhere).
    ``run`` defaults to :class:`subprocess.Popen`; inject it to capture the argv
    without launching anything.
    """
    runner: Runner = run if run is not None else subprocess.Popen
    target = str(path)
    chosen = editor or os.environ.get("EDITOR") or os.environ.get("VISUAL")
    if chosen:
        argv = [chosen, target]
    elif sys.platform == "win32":
        argv = ["cmd", "/c", "start", "", target]
    elif sys.platform == "darwin":
        argv = ["open", target]
    else:
        argv = ["xdg-open", target]
    runner(argv)
    return argv
