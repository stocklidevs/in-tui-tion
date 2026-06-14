"""intui.actions.files: opt-in side-effect helpers an app calls (engine-free)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from intui.actions.files import delete_path, open_in_editor, save_copy


def test_delete_path_removes_file(tmp_path: Path) -> None:
    p = tmp_path / "x.txt"
    p.write_text("hi", encoding="utf-8")
    delete_path(p)
    assert not p.exists()


def test_delete_path_missing_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        delete_path(tmp_path / "ghost.txt")


def test_save_copy_copies_and_returns_dest(tmp_path: Path) -> None:
    src = tmp_path / "a.txt"
    src.write_text("data", encoding="utf-8")
    dst = tmp_path / "sub" / "b.txt"
    dst.parent.mkdir()
    out = save_copy(src, dst)
    assert out == dst and dst.read_text(encoding="utf-8") == "data"


def test_open_in_editor_uses_explicit_editor() -> None:
    calls: list[list[str]] = []
    argv = open_in_editor("src/app.py", editor="vi", run=calls.append)
    assert argv == ["vi", "src/app.py"]
    assert calls == [["vi", "src/app.py"]]


def test_open_in_editor_uses_env_editor(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EDITOR", "nano")
    monkeypatch.delenv("VISUAL", raising=False)
    calls: list[list[str]] = []
    argv = open_in_editor("f.py", run=calls.append)
    assert argv == ["nano", "f.py"]


def test_open_in_editor_falls_back_to_platform_opener(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("EDITOR", raising=False)
    monkeypatch.delenv("VISUAL", raising=False)
    captured: list[list[str]] = []
    argv = open_in_editor("f.py", run=captured.append)
    # some non-empty opener argv that references the path; exact opener is OS-specific
    assert argv and "f.py" in argv and captured == [argv]


def test_open_in_editor_returns_argv_without_launching() -> None:
    # default run would be subprocess.Popen; with an injected run we never launch
    seen: list[Any] = []
    open_in_editor("f.py", editor="code", run=seen.append)
    assert seen and seen[0][0] == "code"
