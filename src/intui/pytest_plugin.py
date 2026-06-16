"""pytest plugin: emit the in-TUI-tion event stream as a test suite runs.

Enable with ``pytest --intui[=PATH]``; **inert** otherwise (it only registers the
option). Auto-discovered via the ``pytest11`` entry point. Maps pytest's hooks
onto the canonical vocabulary through the Producer SDK — modules become tasks,
tests become work items — so the output is ordinary canonical ndjson that
``intui watch`` / ``--follow`` / scrub consume with no adapter.

Engine-free: imports only stdlib + ``intui.emit`` (no terminal engine, and not
even ``pytest`` at import time — pytest discovers the hooks by name).
"""

from __future__ import annotations

import time
import warnings
from typing import Any

from intui.emit import RunRecorder, run_recorder

_DEFAULT_PATH = "intui-pytest.jsonl"


def pytest_addoption(parser: Any) -> None:
    group = parser.getgroup("intui", "in-TUI-tion event stream")
    group.addoption(
        "--intui",
        nargs="?",
        const=_DEFAULT_PATH,
        default=None,
        metavar="PATH",
        help="emit an in-TUI-tion event stream to PATH (default: %(const)r); "
        "watch it with `intui watch PATH`",
    )


def pytest_configure(config: Any) -> None:
    path = config.getoption("intui", default=None)
    if not path:
        return  # inert unless opted in
    try:
        recorder = run_recorder(path, run_id="pytest")
    except OSError as exc:  # bad --intui path: warn, don't break the test run
        warnings.warn(f"--intui: could not open {path!r}: {exc}", stacklevel=2)
        return
    config.pluginmanager.register(_IntuiReporter(recorder), "intui-reporter")


def _module_of(nodeid: str, location: Any) -> str:
    if location and location[0]:
        return str(location[0]).replace("\\", "/")
    return nodeid.split("::", 1)[0]


def _name_of(nodeid: str) -> str:
    return nodeid.split("::", 1)[1] if "::" in nodeid else nodeid


def _short_repr(report: Any) -> str:
    longrepr = getattr(report, "longrepr", None)
    crash = getattr(longrepr, "reprcrash", None)
    message = getattr(crash, "message", None)
    if message:
        return str(message).splitlines()[0][:200]
    text = (getattr(report, "longreprtext", "") or str(longrepr or "")).strip()
    return text.splitlines()[-1][:200] if text else ""


class _IntuiReporter:
    """Translates pytest reporting hooks into canonical events."""

    def __init__(self, recorder: RunRecorder) -> None:
        self._rec = recorder
        self._outcome: dict[str, str] = {}
        self._failrepr: dict[str, str] = {}
        self._passed = 0
        self._failed = 0
        self._skipped = 0
        self._start = time.monotonic()

    def pytest_sessionstart(self, session: Any) -> None:
        self._start = time.monotonic()
        self._rec.run_started(summary="pytest run")

    def pytest_runtest_logstart(self, nodeid: str, location: Any) -> None:
        self._rec.work_item_started(
            nodeid, task_id=_module_of(nodeid, location), title=_name_of(nodeid)
        )

    def pytest_runtest_logreport(self, report: Any) -> None:
        nid = report.nodeid
        if report.failed:
            self._outcome[nid] = "failed"  # setup/call/teardown failure
            self._failrepr[nid] = _short_repr(report)
        elif report.skipped:
            self._outcome.setdefault(nid, "skipped")
        else:
            self._outcome.setdefault(nid, "passed")

    def pytest_runtest_logfinish(self, nodeid: str, location: Any) -> None:
        status = self._outcome.pop(nodeid, "passed")
        self._rec.work_item_completed(nodeid, task_id=_module_of(nodeid, location), status=status)
        if status == "failed":
            self._failed += 1
            detail = self._failrepr.pop(nodeid, "")
            self._rec.system(f"FAILED {nodeid}{': ' + detail if detail else ''}")
        elif status == "skipped":
            self._skipped += 1
        else:
            self._passed += 1

    def pytest_sessionfinish(self, session: Any, exitstatus: Any) -> None:
        total = self._passed + self._failed + self._skipped
        duration = round(time.monotonic() - self._start, 2)
        self._rec.evidence(
            title="pytest summary",
            passed=self._passed,
            failed=self._failed,
            skipped=self._skipped,
            total=total,
            duration=f"{duration}s",
        )
        if self._failed or int(exitstatus) != 0:
            self._rec.run_failed()  # drives the activity strip to "failure"
        else:
            self._rec.run_completed(status="passed")
        self._rec.close()
