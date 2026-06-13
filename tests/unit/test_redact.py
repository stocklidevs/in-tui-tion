"""Redactor — Principle VI, SC-003 (engine-free, headless)."""

from intui.kit.state import redact

MARKER = "‹redacted›"


def test_redacts_windows_absolute_path() -> None:
    out = redact(r"see C:\Users\pstoc\secret\config.toml for details")
    assert r"C:\Users\pstoc" not in out
    assert MARKER in out
    assert "for details" in out  # surrounding safe text kept


def test_redacts_posix_absolute_path() -> None:
    out = redact("loaded /home/alice/.ssh/id_rsa now")
    assert "/home/alice/.ssh/id_rsa" not in out
    assert MARKER in out


def test_redacts_url_with_credentials() -> None:
    out = redact("endpoint https://user:p4ss@api.example.com/v1 used")
    assert "p4ss" not in out
    assert "user:p4ss@api.example.com" not in out
    assert MARKER in out


def test_redacts_token_like_string() -> None:
    out = redact("key sk-abcdef0123456789ABCDEF0123 active")
    assert "sk-abcdef0123456789ABCDEF0123" not in out
    assert MARKER in out


def test_redacts_unsafe_substring_inside_larger_string() -> None:
    out = redact("path=C:\\Users\\me\\x;mode=fast")
    assert "C:\\Users\\me\\x" not in out
    assert "mode=fast" in out  # the safe remainder survives


def test_safe_text_left_intact() -> None:
    text = "pass rate 92% over 14 tasks, 2 failures"
    assert redact(text) == text


def test_relative_path_not_redacted() -> None:
    text = "edited src/app.py and README.md"
    assert redact(text) == text
