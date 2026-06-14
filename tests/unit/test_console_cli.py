"""intui watch CLI: arg parsing (file vs `-- cmd`), options, and clear errors
(no tracebacks) on a missing file or a command that cannot start."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from intui.console import cli

GOOD = {
    "version": "1",
    "event_id": "e1",
    "run_id": "r1",
    "timestamp": "2026-06-14T10:00:00Z",
    "type": "task_started",
    "scope": {"task_id": "t1"},
}


@pytest.fixture(autouse=True)
def _no_terminal(monkeypatch: pytest.MonkeyPatch) -> list[dict[str, Any]]:
    """Replace app.run() with a recorder so no terminal is opened."""
    calls: list[dict[str, Any]] = []

    class _FakeApp:
        def __init__(self, **kw: Any) -> None:
            self.kw = kw

        def run(self) -> None:
            calls.append(self.kw)

    def fake_build(source: Any, *, public_safe: bool = True, **kw: Any) -> _FakeApp:
        return _FakeApp(source=source, public_safe=public_safe)

    monkeypatch.setattr(cli, "build_console", fake_build)
    return calls


def _stream_file(tmp_path: Path) -> Path:
    p = tmp_path / "run.jsonl"
    p.write_text(json.dumps(GOOD) + "\n", encoding="utf-8")
    return p


def test_file_form_runs(tmp_path: Path, _no_terminal: list[dict[str, Any]]) -> None:
    rc = cli.main(["watch", str(_stream_file(tmp_path))])
    assert rc == 0
    assert _no_terminal and _no_terminal[0]["public_safe"] is True


def test_no_public_safe_flag(tmp_path: Path, _no_terminal: list[dict[str, Any]]) -> None:
    rc = cli.main(["watch", "--no-public-safe", str(_stream_file(tmp_path))])
    assert rc == 0
    assert _no_terminal[0]["public_safe"] is False


def test_missing_file_is_clear_error(capsys: pytest.CaptureFixture[str]) -> None:
    rc = cli.main(["watch", "does-not-exist.jsonl"])
    assert rc != 0
    err = capsys.readouterr().err.lower()
    assert "error" in err and "does-not-exist.jsonl" in err
    assert "traceback" not in err


def test_uncstartable_command_is_clear_error(capsys: pytest.CaptureFixture[str]) -> None:
    rc = cli.main(["watch", "--", "this-command-does-not-exist-xyz"])
    assert rc != 0
    err = capsys.readouterr().err.lower()
    assert "error" in err
    assert "traceback" not in err


def test_command_form_runs(_no_terminal: list[dict[str, Any]]) -> None:
    import sys

    rc = cli.main(["watch", "--", sys.executable, "-c", "pass"])
    assert rc == 0
    assert _no_terminal  # built a console over a SubprocessSource


def test_no_target_is_error(capsys: pytest.CaptureFixture[str]) -> None:
    rc = cli.main(["watch"])
    assert rc != 0
