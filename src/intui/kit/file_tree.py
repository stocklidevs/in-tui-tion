"""FileTree: a workspace directory tree (R-workspace).

Wraps the engine's ``Tree`` widget (keyboard navigation, visible cursor,
expand/collapse, scrolling come from it); this component owns the data direction
only — view model in, nodes out — building the nested directory tree recursively
and preserving expansion by node path across refreshes. Public-safe per the
bound selector. State-derived (Principle I): we do NOT walk the live filesystem.
"""

from __future__ import annotations

from typing import Any

from textual.app import ComposeResult
from textual.widgets import Tree
from textual.widgets.tree import TreeNode

from intui.kit.state.workspace import FileNode, FileTreeView
from intui.viewmodels.selector import Selector
from intui.widgets.bound import BoundContainer


class FileTree(BoundContainer):
    DEFAULT_CSS = """
    FileTree { height: auto; }
    FileTree Tree { height: auto; max-height: 100%; }
    """

    def __init__(self, selector: Selector[FileTreeView], **kwargs: Any) -> None:
        super().__init__(selector, **kwargs)
        self._vm = FileTreeView()

    def compose(self) -> ComposeResult:
        tree: Tree[str] = Tree("workspace", id="file-tree")
        tree.show_root = False
        yield tree

    # --- BoundContainer contract --------------------------------------------

    def sync_view(self, vm: FileTreeView) -> None:
        self._vm = vm
        tree = self.query_one(Tree)
        expanded = self._expanded_paths(tree.root)
        tree.clear()
        for node in vm.roots:
            self._add(tree.root, node, expanded)
        tree.root.expand()

    def _add(self, parent: TreeNode[str], node: FileNode, expanded: set[str]) -> None:
        label = self._label(node)
        if node.is_dir:
            branch = parent.add(label, data=node.path, expand=node.path in expanded or True)
            for child in node.children:
                self._add(branch, child, expanded)
        else:
            parent.add_leaf(label, data=node.path)

    @staticmethod
    def _label(node: FileNode) -> str:
        if node.is_dir:
            return f"{node.name}/"
        status = f"  ({node.status})" if node.status else ""
        glyph = f"{node.glyph} " if node.glyph else ""
        return f"{glyph}{node.name}{status}"

    def _expanded_paths(self, root: TreeNode[str]) -> set[str]:
        found: set[str] = set()

        def walk(node: TreeNode[str]) -> None:
            for child in node.children:
                if child.is_expanded and child.data:
                    found.add(str(child.data))
                walk(child)

        walk(root)
        return found

    # --- Introspection (apps and tests) -------------------------------------

    def paths(self) -> list[str]:
        tree = self.query_one(Tree)
        out: list[str] = []

        def walk(node: TreeNode[str]) -> None:
            for child in node.children:
                if child.data:
                    out.append(str(child.data))
                walk(child)

        walk(tree.root)
        return out

    def labels(self) -> list[str]:
        tree = self.query_one(Tree)
        out: list[str] = []

        def walk(node: TreeNode[str]) -> None:
            for child in node.children:
                out.append(str(child.label))
                walk(child)

        walk(tree.root)
        return out
