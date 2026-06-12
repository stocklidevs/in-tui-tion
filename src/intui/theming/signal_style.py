"""Status-to-style resolution for signals: pure, engine-free (FR-018).

The Signal widget renders these styles; the mapping logic lives here so it
is headlessly testable and reusable by any rendering layer.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class MotionMode(Enum):
    STEADY = "steady"
    PULSE = "pulse"
    SWOOSH = "swoosh"
    STROBE = "strobe"


@dataclass(frozen=True, slots=True)
class StatusStyle:
    """How one status renders.

    ``color`` is a theme status-color token (or a literal color). ``glyph``
    and ``label`` are the mandatory non-color counterparts (Principle IV):
    status must never depend on color alone.
    """

    color: str
    motion: MotionMode
    glyph: str
    label: str

    def __post_init__(self) -> None:
        if not self.glyph:
            raise ValueError("StatusStyle.glyph is mandatory (non-color counterpart)")
        if not self.label:
            raise ValueError("StatusStyle.label is mandatory (non-color counterpart)")


UNKNOWN_STATUS_STYLE = StatusStyle(
    color="muted",
    motion=MotionMode.STEADY,
    glyph="·",
    label="unknown",
)


def resolve_status_style(
    status: str,
    styles: dict[str, StatusStyle] | None = None,
    *,
    fallback: StatusStyle = UNKNOWN_STATUS_STYLE,
) -> StatusStyle:
    """Resolve a status to its declared style; unknown statuses fall back to
    a neutral steady style (never crash, never blank)."""
    if styles is None:
        return fallback
    return styles.get(status, fallback)
