"""A tiny sample suite for the pytest → in-TUI-tion demo.

Run it and watch the run as a console::

    pytest examples/pytest_console --intui=run.jsonl
    intui watch run.jsonl          # or: intui watch --follow run.jsonl

(These are intentionally a mix of pass / fail / skip so the console shows all
three states. This file lives under examples/ and is NOT part of intui's own
test suite — `pytest` here only collects `tests/`.)
"""

import pytest


def test_addition() -> None:
    assert 1 + 1 == 2


def test_string() -> None:
    assert "in" in "in-TUI-tion"


def test_intentional_failure() -> None:
    assert sum([1, 2, 3]) == 7, "demo failure: 6 != 7"


@pytest.mark.skip(reason="demo skip")
def test_skipped() -> None:
    raise AssertionError("never runs — this test is skipped")
