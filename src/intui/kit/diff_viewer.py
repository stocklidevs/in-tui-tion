"""DiffViewer: changed-file list + selected-file green/red diff (US1, R8).

A master/detail BoundContainer: the changed-file list (engine ListView, for
keyboard selection + visible focus) and a scrollable diff body for the
selected file. Diff lines carry a `+`/`-`/space marker (the non-color
counterpart) plus theme color. Selection is local UI state, preserved across
refreshes by file path. Rendering is public-safe per the bound selector.
"""

from __future__ import annotations

from typing import Any

from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Horizontal, VerticalScroll
from textual.widgets import ListItem, ListView, Static

from intui.kit.state.artifacts import DiffLine, DiffLineKind, DiffView
from intui.viewmodels.selector import Selector
from intui.widgets.bound import BoundContainer

_MARKERS = {DiffLineKind.ADD: "+", DiffLineKind.REMOVE: "-", DiffLineKind.CONTEXT: " "}
_TOKENS = {
    DiffLineKind.ADD: "success",
    DiffLineKind.REMOVE: "failure",
    DiffLineKind.CONTEXT: "muted",
}
_MAX_LINE = 200


class DiffViewer(BoundContainer):
    DEFAULT_CSS = """
    DiffViewer { height: auto; }
    DiffViewer #diff-files { width: 32; border-right: solid $panel; }
    DiffViewer #diff-body { width: 1fr; padding: 0 1; }
    DiffViewer ListView { height: auto; max-height: 100%; }
    """

    def __init__(self, selector: Selector[DiffView], **kwargs: Any) -> None:
        super().__init__(selector, **kwargs)
        self._view = DiffView()
        self._selected: str | None = None
        self._paths: list[str] = []
        # Bumped each rebuild so freshly mounted item ids never collide with the
        # previous generation while ListView.clear() (async) is still tearing it
        # down — otherwise an incremental multi-file diff raises DuplicateIds.
        self._rebuild_gen = 0

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield ListView(id="diff-files")
            yield VerticalScroll(Static(id="diff-body"), id="diff-body-scroll")

    # --- BoundContainer contract --------------------------------------------

    def sync_view(self, vm: DiffView) -> None:
        self._view = vm
        new_paths = [row.path for row in vm.files]
        if new_paths != self._paths:
            self._paths = new_paths
            self._rebuild_list()
        if self._selected not in new_paths:
            self._selected = new_paths[0] if new_paths else None
        self._render_body()

    def _rebuild_list(self) -> None:
        listview = self.query_one("#diff-files", ListView)
        listview.clear()
        self._rebuild_gen += 1
        gen = self._rebuild_gen
        if not self._view.files:
            listview.append(ListItem(Static("no changes"), id=f"diff_empty_{gen}"))
            return
        for index, row in enumerate(self._view.files):
            if row.no_text_diff:
                label = f"{row.path}  (no text diff)"
            else:
                label = f"{row.path}  (+{row.added} -{row.removed})"
            # Key by generation+index, not path: redaction can collapse distinct
            # paths to the same marker (duplicate ids), and the generation prefix
            # avoids colliding with the previous list during the async clear().
            listview.append(ListItem(Static(label), id=f"file_{gen}_{index}"))

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        item_id = event.item.id or ""
        if item_id.startswith("file_"):
            try:
                # id is "file_{gen}_{index}"; the trailing segment is the index.
                index = int(item_id.rsplit("_", 1)[-1])
            except ValueError:
                return
            if 0 <= index < len(self._paths):
                self._selected = self._paths[index]
                self._render_body()

    def _render_body(self) -> None:
        body = self.query_one("#diff-body", Static)
        if self._selected is None:
            body.update("")
            return
        row = next((r for r in self._view.files if r.path == self._selected), None)
        if row is not None and row.no_text_diff:
            body.update("no text diff")
            return
        lines = self._view.body(self._selected)
        body.update(self._render_lines(lines))

    def _render_lines(self, lines: tuple[DiffLine, ...]) -> Text:
        theme = getattr(self.app, "intui_theme", None)
        text = Text()
        for line in lines:
            marker = _MARKERS[line.kind]
            content = line.text if len(line.text) <= _MAX_LINE else line.text[:_MAX_LINE] + "…"
            color = theme.resolve_color(_TOKENS[line.kind]) if theme is not None else None
            text.append(f"{marker}{content}\n", style=color or "")
        return text

    # --- Introspection (apps and tests) -------------------------------------

    def file_rows(self) -> list[str]:
        rows = []
        for row in self._view.files:
            if row.no_text_diff:
                rows.append(f"{row.path}  (no text diff)")
            else:
                rows.append(f"{row.path}  (+{row.added} -{row.removed})")
        return rows

    def file_list_text(self) -> str:
        return "no changes" if not self._view.files else "\n".join(self.file_rows())

    def selected_path(self) -> str | None:
        return self._selected

    def select_path(self, path: str) -> None:
        if path in self._paths:
            self._selected = path
            self._render_body()

    def body_text(self) -> str:
        if self._selected is None:
            return ""
        row = next((r for r in self._view.files if r.path == self._selected), None)
        if row is not None and row.no_text_diff:
            return "no text diff"
        return self._render_lines(self._view.body(self._selected)).plain
