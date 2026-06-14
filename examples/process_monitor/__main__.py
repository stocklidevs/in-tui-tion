"""Entry point: ``python -m examples.process_monitor``."""

from examples.process_monitor.run import build_app

build_app().run()  # type: ignore[attr-defined]
