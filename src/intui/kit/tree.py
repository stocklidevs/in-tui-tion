"""TaskTree: the two-level task/work-item tree (US2).

Wraps the engine's ``Tree`` widget (keyboard navigation, visible cursor,
scrolling come from it); this component owns the data direction only —
view model in, nodes out — preserving per-task expansion across refreshes
by task key (local UI state, research R5).
"""

from __future__ import annotations

from typing import Any

from textual.app import ComposeResult
from textual.widgets import Tree

from intui.kit.state.selectors import TaskRow, TreeView
from intui.viewmodels.selector import Selector
from intui.widgets.bound import BoundContainer


class TaskTree(BoundContainer):
    DEFAULT_CSS = """
    TaskTree { height: auto; }
    TaskTree Tree { height: auto; max-height: 100%; }
    """

    def __init__(self, selector: Selector[TreeView], **kwargs: Any) -> None:
        super().__init__(selector, **kwargs)
        self._vm = TreeView()

    def compose(self) -> ComposeResult:
        tree: Tree[str] = Tree("tasks", id="task-tree")
        tree.show_root = False
        yield tree

    # --- BoundContainer contract --------------------------------------------

    def sync_view(self, vm: TreeView) -> None:
        self._vm = vm
        tree = self.query_one(Tree)
        expanded_keys = {
            node.data for node in tree.root.children if node.is_expanded and node.data
        }
        tree.clear()
        for task in vm.tasks:
            node = tree.root.add(
                self._task_label(task),
                data=task.key,
                expand=task.key in expanded_keys,
            )
            node.allow_expand = bool(task.items)
            for item in task.items:
                node.add_leaf(f"{item.glyph} {item.label:<8} {item.title}", data=item.key)
        tree.root.expand()

    @staticmethod
    def _task_label(task: TaskRow) -> str:
        return f"{task.glyph} {task.label:<8} {task.title}"

    # --- Introspection helpers (used by apps and tests) ----------------------

    def task_labels(self) -> list[str]:
        tree = self.query_one(Tree)
        return [str(node.label) for node in tree.root.children]

    def visible_item_count(self) -> int:
        tree = self.query_one(Tree)
        return sum(len(node.children) for node in tree.root.children if node.is_expanded)

    def _task_node(self, key: str) -> Any:
        tree = self.query_one(Tree)
        for node in tree.root.children:
            if node.data == key:
                return node
        raise KeyError(key)

    def expand_task(self, key: str) -> None:
        self._task_node(key).expand()

    def collapse_task(self, key: str) -> None:
        self._task_node(key).collapse()

    def is_expanded(self, key: str) -> bool:
        return bool(self._task_node(key).is_expanded)

    def item_labels(self, key: str) -> list[str]:
        return [str(child.label) for child in self._task_node(key).children]
