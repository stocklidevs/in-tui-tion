"""FileTree: a workspace directory tree (R-workspace).

Wraps the engine's ``Tree`` widget (keyboard navigation, visible cursor,
expand/collapse, scrolling come from it); this component owns the data direction
only — view model in, nodes out — building the nested directory tree recursively
and preserving expansion by node path across refreshes. Public-safe per the
bound selector. State-derived (Principle I): we do NOT walk the live filesystem.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from textual.app import ComposeResult
from textual.binding import Binding
from textual.widgets import Tree
from textual.widgets.tree import TreeNode

from intui.kit.state.workspace import (
    FileNode,
    FileTreeView,
    copy_path_intent,
    delete_file_intent,
    open_file_intent,
)
from intui.viewmodels.selector import Selector
from intui.widgets.bound import BoundContainer

if TYPE_CHECKING:
    from intui.app import IntuiApp


class FileTree(BoundContainer):
    DEFAULT_CSS = """
    FileTree { height: auto; }
    FileTree Tree { height: auto; max-height: 100%; }
    """

    # Action keys for the selected file. The library only POSTS intents — the
    # application decides whether/how to act (Principle III). Delete is risky and
    # routes through the built-in confirmation. Keys avoid the console view keys.
    BINDINGS = [
        Binding("o", "open_file", "Open"),
        Binding("c", "copy_path", "Copy path"),
        Binding("x", "delete_file", "Delete"),
    ]

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

    # --- File actions (posted as intents; the app fulfills) ------------------

    def selected_file(self) -> str | None:
        """The path of the currently-selected file, or ``None`` for a directory
        / no selection."""
        node = self.query_one(Tree).cursor_node
        if node is None or node.allow_expand or not node.data:
            return None  # directory or nothing selected
        return str(node.data)

    def action_open_file(self) -> None:
        self._post(open_file_intent)

    def action_copy_path(self) -> None:
        self._post(copy_path_intent)

    def action_delete_file(self) -> None:
        self._post(delete_file_intent)

    def _post(self, make_intent: Any) -> None:
        path = self.selected_file()
        if path is None:
            return  # no-op on a directory / empty selection
        cast("IntuiApp", self.app).post_intent(make_intent(path))

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
