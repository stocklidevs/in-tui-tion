"""Run: ``uv run python -m examples.intentforge_console`` (or ``intui watch
--adapter intentforge examples/intentforge_console/run.ndjson``)."""

from examples.intentforge_console.app import build_app

build_app().run()
