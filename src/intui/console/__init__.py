"""intui.console: the batteries-included, zero-config console runner.

This subpackage is the rendering-layer front door — ``ConsoleApp``, the
``watch()`` one-liner, and the ``intui watch`` CLI. It imports Textual and the
kit, so it is deliberately NOT re-exported from the engine-free ``intui`` root
(importing ``intui`` must stay terminal-free; Constitution Principle II).
"""

from intui.console.app import ConsoleApp, build_console
from intui.console.runner import watch

__all__ = ["ConsoleApp", "build_console", "watch"]
