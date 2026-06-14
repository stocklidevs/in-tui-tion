"""intentforge_console: the IntentForge adapter end-to-end (feature 010).

Builds the zero-config :class:`ConsoleApp` (feature 009) over an
:class:`IntentForgeSource` that adapts a captured IntentForge ndjson stream into
the canonical vocabulary — proving "point the runner at a real IF run, get a
console" with no IF-specific code in the console or the kit.
"""

from __future__ import annotations

from pathlib import Path

from intui.adapters import IntentForgeSource
from intui.console import ConsoleApp, build_console

RECORDING = Path(__file__).parent / "run.ndjson"


def build_app(*, public_safe: bool = True) -> ConsoleApp:
    return build_console(IntentForgeSource(RECORDING), public_safe=public_safe)


if __name__ == "__main__":
    build_app().run()
