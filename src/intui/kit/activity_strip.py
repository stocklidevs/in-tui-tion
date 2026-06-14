"""ActivityStrip: the signature full-width KITT activity indicator (US2, R6).

A preset of the Signal primitive bound to an activity-state selector, using the
engine-free ``ACTIVITY_STYLES`` R6 mapping. The track spans the available width
(recomputed on resize, with the state label always kept). Unknown states fall
back to a neutral steady style that keeps the raw name (via ``activity_style``).
"""

from __future__ import annotations

from typing import Any

from intui.kit.state.activity import ACTIVITY_STYLES, activity_style
from intui.theming.signal_style import StatusStyle
from intui.viewmodels.selector import Selector
from intui.widgets.signal import Signal

_LABEL_RESERVE = 16  # space kept for "  glyph label" beside the track
_MIN_TRACK = 6


class ActivityStrip(Signal):
    DEFAULT_CSS = """
    ActivityStrip { height: 1; width: 1fr; }
    """

    def __init__(self, selector: Selector[str], *, swoosh_glow: int = 4, **kwargs: Any) -> None:
        # A wider glow than a small inline Signal — this is the marquee KITT bar.
        super().__init__(
            selector, dict(ACTIVITY_STYLES), track_width=12, swoosh_glow=swoosh_glow, **kwargs
        )

    def _current_style(self) -> StatusStyle:
        # Use the activity mapping so unknown states keep their raw label
        # (Signal's default fallback would relabel them "unknown").
        return activity_style(self._status)

    def on_resize(self) -> None:
        width = self.size.width
        if width:
            self._track_width = max(width - _LABEL_RESERVE, _MIN_TRACK)
            self.update(self._render_frame())
