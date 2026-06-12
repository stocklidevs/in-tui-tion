"""The default dark theme (token values finalized in the theming story)."""

from intui.theming.theme import Theme

DEFAULT_THEME = Theme(
    name="intui-dark",
    palette={
        "background": "#0d1117",
        "surface": "#161b22",
        "text": "#e6edf3",
        "text-muted": "#8b949e",
    },
    emphasis={
        "accent": "#58a6ff",
        "muted": "#30363d",
    },
    status_colors={
        "thinking": "#f85149",
        "waiting": "#d29922",
        "verifying": "#39c5cf",
        "success": "#3fb950",
        "history": "#bc8cff",
        "failure": "#f85149",
    },
)
