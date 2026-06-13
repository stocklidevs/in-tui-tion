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

    def status_color(self, status: str) -> str:
        """Resolve a status token to a color; unknown statuses are muted."""
        return self.status_colors.get(status, self.emphasis.get("muted", "#808080"))

    def resolve_color(self, token: str) -> str:
        """Resolve any token (status, emphasis, palette, or literal color)."""
        if token.startswith("#"):
            return token
        for group in (self.status_colors, self.emphasis, self.palette):
            if token in group:
                return group[token]
        return self.emphasis.get("muted", "#808080")

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Theme):
            return NotImplemented
        return (
            self.name == other.name
            and dict(self.palette) == dict(other.palette)
            and dict(self.emphasis) == dict(other.emphasis)
            and dict(self.status_colors) == dict(other.status_colors)
        )
