"""process_monitor: spawn a short workload and watch its resources (feature 015).

Run it::

    uv run python -m examples.process_monitor      # press `m` for the metrics view

Needs the metrics extra (``pip install 'in-tui-tion[metrics]'``). Equivalent CLI::

    intui watch --metrics -- python -c "<workload>"
"""

from __future__ import annotations

import sys

from intui.console import build_console
from intui.events import ProcessMonitorSource

# A brief CPU/memory workload so there is something to watch.
_WORKLOAD = (
    "import time\n"
    "buf = []\n"
    "for i in range(6):\n"
    "    buf.append(bytearray(2_000_000))  # grow memory\n"
    "    sum(range(2_000_00))              # burn a little CPU\n"
    "    time.sleep(0.15)\n"
)


def build_app() -> object:
    source = ProcessMonitorSource([sys.executable, "-c", _WORKLOAD], interval=0.1)
    return build_console(source)


if __name__ == "__main__":
    build_app().run()  # type: ignore[attr-defined]
