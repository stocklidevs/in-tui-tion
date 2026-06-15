"""Timeline: the engine-free scrub cursor controller (pure)."""

from __future__ import annotations

from intui.state import Timeline


def test_default_is_live() -> None:
    tl = Timeline()
    assert tl.live is True
    assert tl.position(total=10) == 10  # live follows the end


def test_pause_freezes_at_total() -> None:
    tl = Timeline().pause(total=10)
    assert tl.live is False
    assert tl.position(total=10) == 10
    assert tl.position(total=12) == 10  # frozen even as total grows


def test_step_clamps() -> None:
    tl = Timeline().pause(total=10)
    tl = tl.step(-1, total=10)
    assert tl.position(total=10) == 9
    tl = tl.step(-100, total=10)
    assert tl.position(total=10) == 0
    tl = tl.step(50, total=10)
    assert tl.position(total=10) == 10


def test_step_from_live_pauses_relative_to_total() -> None:
    tl = Timeline().step(-1, total=10)  # stepping back from live
    assert tl.live is False
    assert tl.position(total=10) == 9


def test_to_start_and_to_end() -> None:
    tl = Timeline().to_start()
    assert tl.live is False and tl.position(total=10) == 0
    tl = tl.to_end()
    assert tl.live is True and tl.position(total=10) == 10


def test_toggle() -> None:
    live = Timeline()
    paused = live.toggle(total=7)
    assert paused.live is False and paused.position(total=7) == 7
    back = paused.toggle(total=7)
    assert back.live is True


def test_resume() -> None:
    assert Timeline().pause(total=5).resume().live is True


def test_immutability() -> None:
    tl = Timeline()
    stepped = tl.step(-1, total=5)
    assert tl.live is True and stepped is not tl


def test_label() -> None:
    assert "live" in Timeline().label(total=10).lower()
    paused = Timeline().pause(total=10).step(-3, total=10)
    label = paused.label(total=10)
    assert "7" in label and "10" in label
