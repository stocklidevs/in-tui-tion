"""intui.kit: the high-level component kit (layer 2).

Component classes are imported lazily so that ``intui.kit.state`` (the
engine-free model core) can be imported without pulling in the terminal
engine — the layering guard depends on this.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from intui.kit.chip import TaskCounterChip
    from intui.kit.command_bar import CommandBar
    from intui.kit.command_palette import CommandPalette
    from intui.kit.diff_viewer import DiffViewer
    from intui.kit.evidence_panel import EvidencePanel
    from intui.kit.lanes import LanesPanel
    from intui.kit.tree import TaskTree

__all__ = [
    "CommandBar",
    "CommandPalette",
    "DiffViewer",
    "EvidencePanel",
    "LanesPanel",
    "TaskCounterChip",
    "TaskTree",
]

_LAZY = {
    "TaskCounterChip": ("intui.kit.chip", "TaskCounterChip"),
    "TaskTree": ("intui.kit.tree", "TaskTree"),
    "LanesPanel": ("intui.kit.lanes", "LanesPanel"),
    "CommandBar": ("intui.kit.command_bar", "CommandBar"),
    "CommandPalette": ("intui.kit.command_palette", "CommandPalette"),
    "DiffViewer": ("intui.kit.diff_viewer", "DiffViewer"),
    "EvidencePanel": ("intui.kit.evidence_panel", "EvidencePanel"),
}


def __getattr__(name: str) -> object:
    target = _LAZY.get(name)
    if target is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    import importlib

    return getattr(importlib.import_module(target[0]), target[1])


def __dir__() -> list[str]:
    return sorted(__all__)
