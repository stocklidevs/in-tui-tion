"""Theme tokens (foundation stub; completed in the theming user story).

A Theme is a named token set applied application-wide. Widgets reference
tokens, never literal colors, so switching themes requires no widget changes
(FR-017).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field


def _empty() -> Mapping[str, str]:
    return {}


@dataclass(frozen=True, slots=True)
class Theme:
    name: str
    palette: Mapping[str, str] = field(default_factory=_empty)
    emphasis: Mapping[str, str] = field(default_factory=_empty)
    status_colors: Mapping[str, str] = field(default_factory=_empty)
