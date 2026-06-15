"""Timeline: a pure cursor controller for time-travel scrubbing (engine-free).

The cursor is either *live* (``cursor is None`` — follow the end of the stream)
or paused at an index. Operations return new instances; ``position(total)`` is
clamped to the current total (which grows on a live stream), so the controller
needs no knowledge of the moving total until asked. Pairs with
:meth:`Store.snapshot_at` to render historical state.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Timeline:
    cursor: int | None = None  # None = live (follow the end)

    @property
    def live(self) -> bool:
        return self.cursor is None

    def position(self, total: int) -> int:
        """The effective event index to show: ``total`` when live, else clamped."""
        if self.cursor is None:
            return total
        return max(0, min(self.cursor, total))

    def pause(self, total: int) -> Timeline:
        """Freeze at the current position (the latest when coming from live)."""
        return Timeline(self.position(total))

    def resume(self) -> Timeline:
        """Follow the live end again."""
        return Timeline(None)

    def toggle(self, total: int) -> Timeline:
        return self.resume() if not self.live else self.pause(total)

    def step(self, delta: int, total: int) -> Timeline:
        """Move the (paused) cursor by ``delta`` events, clamped to [0, total]."""
        return Timeline(max(0, min(self.position(total) + delta, total)))

    def to_start(self) -> Timeline:
        return Timeline(0)

    def to_end(self) -> Timeline:
        return Timeline(None)

    def label(self, total: int) -> str:
        if self.live:
            return f"▶ live · {total} events"
        return f"⏸ paused {self.position(total)} / {total}"
