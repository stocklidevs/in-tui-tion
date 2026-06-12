"""Constitution Principle II guard: the pipeline core imports no terminal engine.

Only ``intui.widgets`` and ``intui.app`` may import Textual. This test imports
every module in the engine-free subpackages and asserts that doing so does not
pull ``textual`` (or ``rich``) into ``sys.modules``.
"""

import importlib
import pkgutil
import subprocess
import sys

CORE_PACKAGES = [
    "intui.events",
    "intui.state",
    "intui.viewmodels",
    "intui.actions",
    "intui.theming",
]

BANNED_PREFIXES = ("textual", "rich")


def _walk_modules(package_name: str) -> list[str]:
    package = importlib.import_module(package_name)
    names = [package_name]
    for info in pkgutil.walk_packages(package.__path__, prefix=f"{package_name}."):
        names.append(info.name)
    return names


def test_core_packages_do_not_import_terminal_engine() -> None:
    modules = [name for pkg in CORE_PACKAGES for name in _walk_modules(pkg)]
    # Run in a subprocess so this test is immune to engine modules imported
    # by other tests in the same session.
    code = (
        "import importlib, sys\n"
        f"for name in {modules!r}:\n"
        "    importlib.import_module(name)\n"
        f"leaked = sorted(m for m in sys.modules if m.partition('.')[0] in {BANNED_PREFIXES!r})\n"
        "assert not leaked, f'engine modules leaked into core import: {leaked}'\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, check=False
    )
    assert result.returncode == 0, result.stderr
