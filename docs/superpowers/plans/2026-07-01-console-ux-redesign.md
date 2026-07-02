# Console UX Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the console's side "chat window" + one-at-a-time ViewRouter with a single-column run timeline, a floor-pinned prompt with a slash-command palette, a state-colored KITT swoosh, inline diff expansion, and slash-command panel overlays — all in the `intui.console` rendering layer, leaving events/state/reducers/selectors and the kit widgets unchanged.

**Architecture:** A new engine-free selector (`run_timeline_view`) merges the existing conversation / taskboard / artifacts / run-status slices into an ordered list of `TimelineRow` view-models. A new `RunTimeline` rendering widget (in `intui.console`) renders those rows with glyph+label status, an inline-expandable diff region, and a one-shot failure flash. `ConsoleApp.compose` is rewired: `Header → ActivityStrip (state-colored) → RunTimeline (1fr) → SlashPalette → PromptInput → Footer`. Browsable panels (files/metrics/lanes/evidence/tasks) open as modal `Screen` overlays via slash commands; the diff opens inline. No core-layer file changes.

**Tech Stack:** Python 3.11–3.13, Textual 6.x, Rich, pytest (`app.run_test()` harness), ruff, mypy, uv.

## Global Constraints

- Layering (Principle II): new selector code is engine-free (`intui.viewmodels`/`intui.kit.state` may import NO Textual); only `intui.console` / `intui.widgets` import Textual. The root-import guard in `tests/unit/test_layering.py` must stay green.
- Accessibility (Principle IV): every status renders a **glyph + text label**, never color alone. Keyboard-first: all overlays reachable by key and closable with Esc. Honor `MotionMode` (reduced-motion → static).
- Public-safe (Principle VI): diff/evidence/file rendering stays redacted by default; the `public_safe` flag threads through unchanged.
- Test-first (Principle VII): every task writes the failing test first; the run reduces from the canonical stream with no new event types.
- Gate after every task: `uv run pytest && uv run ruff check && uv run ruff format --check && uv run mypy`.
- Commit message trailer: `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`.
- Branch: `020-console-ux-redesign` (already created).
- Verified existing signatures to build on:
  - `conversation_view() -> Selector[ConversationView]`; `ConversationView.entries: tuple[ConversationRow, ...]`; `ConversationRow(order:int, role:str, kind:ConversationKind, text:str, tag:str)`.
  - `tree_view() -> Selector[...]`; result has `.tasks`, each task has `.title:str`, `.status:str`.
  - `diff_view(public_safe=...)`, `evidence_view(...)`, `file_tree_view(...)`, `lanes_view()`, `metrics_view(...)`, `chip_view()` — used unchanged.
  - `run_status_slice()` reduces to a status string (`idle`/`thinking`/`waiting`/`verifying`/`success`/`failure`/`history`).
  - `Signal(selector, *, styles, track_width, swoosh_glow, fps, sweep_seconds)` renders bright `█` core + `▓▒░` glow; motion per `resolve_status_style(status, styles).motion` (SWOOSH/PULSE/STROBE/STEADY).
  - `ConsoleApp(store=, source=, public_safe=, sweep_seconds=, file_actions=)`; `build_console(source, *, public_safe, sweep_seconds, file_actions)`.

---

## Task 1: `TimelineRow` view-model + `run_timeline_view` selector

Merge conversation + task + artifact activity into one ordered, presentation-ready list. Engine-free; this is the data behind the single column.

**Files:**
- Create: `src/intui/kit/state/timeline_feed.py`
- Modify: `src/intui/kit/state/__init__.py` (export `TimelineRow`, `TimelineFeedView`, `run_timeline_view`)
- Test: `tests/unit/test_timeline_feed.py`

**Interfaces:**
- Consumes: `Snapshot.slice("conversation")` (`ConversationState.entries`), `Snapshot.slice("taskboard")` (`.work_items: dict[str, WorkItem]` with `.title`, `.status`), `Snapshot.slice("run_status")` (str). Confirm the taskboard field names against `src/intui/kit/state/` before writing (the plugin test at `tests/unit/test_pytest_plugin.py:68-69` reads `board.work_items.values()` with `.title`/`.status` — use those).
- Produces:
  - `TimelineRow(order:int, kind:str, glyph:str, label:str, text:str, status:str, ref:str)` — frozen dataclass. `kind ∈ {"message","task","failure","milestone"}`; `ref` is a diff id for failure rows that have one, else `""`.
  - `TimelineFeedView(rows: tuple[TimelineRow, ...])` — frozen dataclass.
  - `run_timeline_view() -> Selector[TimelineFeedView]`.
  - `STATUS_GLYPH: dict[str,str]` mapping `passed→"✓" failed→"✗" running→"◷" skipped→"◌" completed→"✓" blocked→"⊘"` (fallback `"◆"`).

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_timeline_feed.py
from __future__ import annotations

from intui.events import read_recording
from intui.kit.state import (
    conversation_slice,
    run_status_slice,
    run_timeline_view,
    taskboard_slice,
)
from intui.state import Store, compose_reducers


def _store_from(path):
    store = Store(
        compose_reducers(
            taskboard=taskboard_slice(),
            conversation=conversation_slice(),
            run_status=run_status_slice(),
        )
    )
    for event in read_recording(path):
        store.ingest(event)
    return store


def test_rows_are_ordered_and_carry_glyph_and_label(tmp_path):
    # Reuse the pytest-plugin fixture shape: a pass, a fail, a skip.
    from intui.emit import run_recorder

    out = tmp_path / "run.jsonl"
    rec = run_recorder(out, run_id="t")
    rec.run_started(summary="pytest run")
    rec.work_item_started("m::test_ok", task_id="m.py", title="test_ok")
    rec.work_item_completed("m::test_ok", task_id="m.py", status="completed")
    rec.work_item_started("m::test_bad", task_id="m.py", title="test_bad")
    rec.work_item_completed("m::test_bad", task_id="m.py", status="failed")
    rec.system("FAILED m::test_bad: assert 1 == 2")
    rec.run_failed()
    rec.close()

    store = _store_from(out)
    view = run_timeline_view()(store.snapshot)

    # ordered, non-empty
    assert view.rows
    assert [r.order for r in view.rows] == sorted(r.order for r in view.rows)
    # every row has a non-empty glyph AND label (Principle IV: never color alone)
    assert all(r.glyph and r.label for r in view.rows)
    # the failed work item surfaces as a failure row
    fails = [r for r in view.rows if r.kind == "failure"]
    assert any("test_bad" in r.text for r in fails)
    assert all(r.glyph == "✗" for r in fails)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_timeline_feed.py -v`
Expected: FAIL — `ImportError: cannot import name 'run_timeline_view'`.

- [ ] **Step 3: Write the selector + view-models**

```python
# src/intui/kit/state/timeline_feed.py
"""Run timeline feed: merge conversation + taskboard into one ordered column.

Engine-free presentation model. The console renders these rows top-to-bottom;
each row is self-describing (glyph + label + text) so status never relies on
color alone (Principle IV).
"""

from __future__ import annotations

from dataclasses import dataclass

from intui.state.snapshot import Snapshot
from intui.viewmodels.selector import Selector, selector

STATUS_GLYPH: dict[str, str] = {
    "passed": "✓",
    "completed": "✓",
    "failed": "✗",
    "running": "◷",
    "started": "◷",
    "skipped": "◌",
    "blocked": "⊘",
}
_FALLBACK_GLYPH = "◆"


@dataclass(frozen=True, slots=True)
class TimelineRow:
    order: int
    kind: str  # "message" | "task" | "failure" | "milestone"
    glyph: str
    label: str
    text: str
    status: str
    ref: str  # diff id for failures that carry one, else ""


@dataclass(frozen=True, slots=True)
class TimelineFeedView:
    rows: tuple[TimelineRow, ...] = ()


def _glyph_for(status: str) -> str:
    return STATUS_GLYPH.get(status, _FALLBACK_GLYPH)


@selector
def run_timeline_view(snapshot: Snapshot) -> TimelineFeedView:
    rows: list[TimelineRow] = []
    order = 0

    board = snapshot.slice("taskboard")
    for wi in board.work_items.values():
        status = str(getattr(wi, "status", ""))
        kind = "failure" if status == "failed" else "task"
        rows.append(
            TimelineRow(
                order=order,
                kind=kind,
                glyph=_glyph_for(status),
                label=status or "task",
                text=str(getattr(wi, "title", "")),
                status=status,
                ref=str(getattr(wi, "id", "")),
            )
        )
        order += 1

    convo = snapshot.slice("conversation")
    for entry in convo.entries:
        text = str(getattr(entry, "text", ""))
        is_fail = "FAILED" in text
        rows.append(
            TimelineRow(
                order=order,
                kind="failure" if is_fail else "message",
                glyph="✗" if is_fail else "›",
                label=str(getattr(entry, "role", "system")),
                text=text,
                status="failed" if is_fail else "",
                ref="",
            )
        )
        order += 1

    return TimelineFeedView(rows=tuple(rows))
```

Note: keep failure rows' glyph `"✗"` regardless of source (test asserts this). The `conversation` FAILED lines carry the human-readable detail; task rows carry the item. Confirm `board.work_items` value attribute names (`title`, `status`, `id`) in `src/intui/kit/state/` — adjust the `getattr` keys only if the source differs.

- [ ] **Step 4: Export from the state package**

```python
# src/intui/kit/state/__init__.py  — add to imports and __all__
from intui.kit.state.timeline_feed import (
    STATUS_GLYPH,
    TimelineFeedView,
    TimelineRow,
    run_timeline_view,
)
# ...and add "STATUS_GLYPH", "TimelineFeedView", "TimelineRow", "run_timeline_view" to __all__
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `uv run pytest tests/unit/test_timeline_feed.py -v`
Expected: PASS (2 passed).

- [ ] **Step 6: Gate + commit**

```bash
uv run pytest && uv run ruff check && uv run ruff format --check && uv run mypy
git add src/intui/kit/state/timeline_feed.py src/intui/kit/state/__init__.py tests/unit/test_timeline_feed.py
git commit -m "feat: run_timeline_view — ordered glyph+label feed model (020)

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

## Task 2: `RunTimeline` widget (single-column feed rendering)

Render the feed rows in the center column, replacing `ConversationLog` + `ViewRouter` as the primary surface. Rendering layer; test via the `app.run_test()` harness like `tests/integration/test_console_app.py`.

**Files:**
- Create: `src/intui/console/timeline_widget.py`
- Modify: `src/intui/console/__init__.py` (export `RunTimeline`)
- Test: `tests/unit/test_run_timeline_widget.py`

**Interfaces:**
- Consumes: `run_timeline_view()` (Task 1), `TimelineFeedView`, `TimelineRow`.
- Produces: `RunTimeline(selector: Selector[TimelineFeedView], **kwargs)` — a `BoundContainer` subclass with `.log_text() -> str` (mirrors `ConversationLog.log_text`, used for assertions) and `sync_view(vm)` that repaints a `#timeline-body` `Static` and auto-scrolls a `#timeline-scroll` `VerticalScroll`.

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_run_timeline_widget.py
from __future__ import annotations

from intui.console.timeline_widget import RunTimeline
from intui.kit.state import TimelineFeedView, TimelineRow, run_timeline_view


def test_build_text_shows_glyph_label_and_text():
    tl = RunTimeline(run_timeline_view())
    tl._view = TimelineFeedView(
        rows=(
            TimelineRow(0, "task", "✓", "completed", "test_ok", "completed", ""),
            TimelineRow(1, "failure", "✗", "failed", "FAILED test_bad", "failed", ""),
        )
    )
    text = tl.log_text()
    assert "✓" in text and "completed" in text and "test_ok" in text
    assert "✗" in text and "FAILED test_bad" in text


def test_empty_state():
    tl = RunTimeline(run_timeline_view())
    tl._view = TimelineFeedView(rows=())
    assert "waiting for events" in tl.log_text().lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_run_timeline_widget.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'intui.console.timeline_widget'`.

- [ ] **Step 3: Implement the widget**

```python
# src/intui/console/timeline_widget.py
"""RunTimeline: the single-column run feed (replaces the side chat window)."""

from __future__ import annotations

from typing import Any

from rich.text import Text
from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Static

from intui.kit.state import TimelineFeedView
from intui.viewmodels.selector import Selector
from intui.widgets.bound import BoundContainer


class RunTimeline(BoundContainer):
    DEFAULT_CSS = """
    RunTimeline { height: 1fr; }
    RunTimeline #timeline-scroll { height: 1fr; }
    RunTimeline #timeline-body { padding: 0 1; }
    """

    def __init__(self, selector: Selector[TimelineFeedView], **kwargs: Any) -> None:
        super().__init__(selector, **kwargs)
        self._view = TimelineFeedView()

    def compose(self) -> ComposeResult:
        yield VerticalScroll(Static(id="timeline-body"), id="timeline-scroll")

    def sync_view(self, vm: TimelineFeedView) -> None:
        self._view = vm
        self.query_one("#timeline-body", Static).update(self._build_text())
        self.query_one("#timeline-scroll", VerticalScroll).scroll_end(animate=False)

    def _build_text(self) -> Text:
        if not self._view.rows:
            return Text("waiting for events…", style="dim")
        theme = getattr(self.app, "intui_theme", None)
        text = Text()
        for i, row in enumerate(self._view.rows):
            if i:
                text.append("\n")
            color = self._row_color(theme, row.status)
            text.append(f"{row.glyph} ", style=color or "")
            text.append(row.text)
            if row.label and row.kind in ("task", "failure"):
                text.append(f"  [{row.label}]", style="dim")
        return text

    def _row_color(self, theme: Any, status: str) -> str | None:
        if theme is None:
            return None
        key = {"failed": "failure", "completed": "success", "passed": "success"}.get(status)
        return theme.resolve_color(key) if key else None

    def log_text(self) -> str:
        return self._build_text().plain
```

- [ ] **Step 4: Export it**

```python
# src/intui/console/__init__.py — add
from intui.console.timeline_widget import RunTimeline
# add "RunTimeline" to __all__
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `uv run pytest tests/unit/test_run_timeline_widget.py -v`
Expected: PASS (2 passed).

- [ ] **Step 6: Gate + commit**

```bash
uv run pytest && uv run ruff check && uv run ruff format --check && uv run mypy
git add src/intui/console/timeline_widget.py src/intui/console/__init__.py tests/unit/test_run_timeline_widget.py
git commit -m "feat: RunTimeline widget renders the single-column feed (020)

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

## Task 3: State-colored KITT swoosh (Signal styles per run phase)

Make the `ActivityStrip`/`Signal` color+motion track the run phase (red `thinking`/`failure`, cyan `verifying`, amber `waiting`, green `success`), so motion is meaningful (Principle V) and never the sole signal (a label sits beside it).

**Files:**
- Create: `src/intui/console/motion.py` (a `CONSOLE_SIGNAL_STYLES` mapping + `activity_label_view` selector)
- Test: `tests/unit/test_console_motion.py`

**Interfaces:**
- Consumes: `run_status_slice()` value (str); `resolve_status_style(status, styles)` from `intui.theming`; `StatusStyle`, `MotionMode`.
- Produces:
  - `CONSOLE_SIGNAL_STYLES: dict[str, StatusStyle]` covering `thinking, verifying, waiting, success, failure, history, idle`.
  - `activity_label_view() -> Selector[str]` returning `"{glyph} {phase}"` (e.g. `"◆ thinking"`) for the label beside the strip.

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_console_motion.py
from __future__ import annotations

from intui.console.motion import CONSOLE_SIGNAL_STYLES, activity_label_view
from intui.state.snapshot import Snapshot
from intui.theming import MotionMode, resolve_status_style


def test_each_phase_has_a_distinct_color_and_motion():
    for phase in ("thinking", "verifying", "waiting", "success", "failure"):
        style = resolve_status_style(phase, CONSOLE_SIGNAL_STYLES)
        assert style.glyph  # glyph present (label-beside guarantee)
        assert isinstance(style.motion, MotionMode)
    # thinking/failure are the "red" family; success is not
    assert CONSOLE_SIGNAL_STYLES["thinking"].color == CONSOLE_SIGNAL_STYLES["failure"].color
    assert CONSOLE_SIGNAL_STYLES["success"].color != CONSOLE_SIGNAL_STYLES["thinking"].color


def test_activity_label_pairs_glyph_with_phase():
    snap = Snapshot(slices={"run_status": "thinking"})
    label = activity_label_view()(snap)
    assert "thinking" in label
    assert label.split()[0]  # a leading glyph token
```

Note: confirm the `Snapshot(slices=...)` construction against `src/intui/state/snapshot.py`; if the constructor differs, build the snapshot the way `tests/unit/test_run_status_slice.py` does and read the phase from there.

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_console_motion.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'intui.console.motion'`.

- [ ] **Step 3: Implement the style map + label selector**

```python
# src/intui/console/motion.py
"""Console motion language: phase → Signal style, and the strip's text label.

Motion is meaningful (Principle V) but never the only signal — the phase label
selector renders a glyph + word beside the strip (Principle IV).
"""

from __future__ import annotations

from intui.state.snapshot import Snapshot
from intui.theming import MotionMode, StatusStyle
from intui.viewmodels.selector import selector

_RED = "#f85149"
_CYAN = "#39c5cf"
_AMBER = "#d29922"
_GREEN = "#3fb950"
_PURPLE = "#bc8cff"
_MUTED = "#8b949e"

CONSOLE_SIGNAL_STYLES: dict[str, StatusStyle] = {
    "thinking": StatusStyle(glyph="◆", label="thinking", color=_RED, motion=MotionMode.SWOOSH),
    "failure": StatusStyle(glyph="✗", label="failure", color=_RED, motion=MotionMode.PULSE),
    "verifying": StatusStyle(glyph="◷", label="verifying", color=_CYAN, motion=MotionMode.SWOOSH),
    "waiting": StatusStyle(glyph="◌", label="waiting", color=_AMBER, motion=MotionMode.STEADY),
    "success": StatusStyle(glyph="✓", label="success", color=_GREEN, motion=MotionMode.PULSE),
    "history": StatusStyle(glyph="⟲", label="history", color=_PURPLE, motion=MotionMode.STEADY),
    "idle": StatusStyle(glyph="·", label="idle", color=_MUTED, motion=MotionMode.STEADY),
}


@selector
def activity_label_view(snapshot: Snapshot) -> str:
    phase = str(snapshot.slice("run_status"))
    style = CONSOLE_SIGNAL_STYLES.get(phase, CONSOLE_SIGNAL_STYLES["idle"])
    return f"{style.glyph} {style.label}"
```

Note: confirm `StatusStyle`'s field names (`glyph`, `label`, `color`, `motion`) against `src/intui/theming/`. If `StatusStyle` uses different names, match them here and in the test.

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/unit/test_console_motion.py -v`
Expected: PASS (2 passed).

- [ ] **Step 5: Gate + commit**

```bash
uv run pytest && uv run ruff check && uv run ruff format --check && uv run mypy
git add src/intui/console/motion.py tests/unit/test_console_motion.py
git commit -m "feat: console motion language — phase-colored KITT + label (020)

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

## Task 4: Panel overlays via slash commands (files/metrics/lanes/evidence/tasks)

Browsable panels open as modal `Screen` overlays over the timeline; Esc closes. Preserve the existing single-key accelerators (t/l/f/m/e) by mapping them to overlay-open actions.

**Files:**
- Create: `src/intui/console/overlays.py` (`PanelOverlay(Screen)` hosting one bound panel widget)
- Modify: `src/intui/console/app.py` (add `action_open_panel`, wire keys)
- Test: `tests/integration/test_console_overlays.py`

**Interfaces:**
- Consumes: existing panel factories `FileTree(file_tree_view(...))`, `MetricsPanel(metrics_view(...))`, `LanesPanel(lanes_view())`, `EvidencePanel(evidence_view(...))`, `TaskTree(tree_view())`.
- Produces: `PanelOverlay(title: str, panel: Widget)` — a `ModalScreen` with `BINDINGS = [("escape", "dismiss", "Close")]`, rendering the panel under a titled border. `ConsoleApp.action_open_panel(name: str)` pushes the overlay for `name ∈ {"files","metrics","lanes","evidence","tasks"}`.

- [ ] **Step 1: Write the failing test**

```python
# tests/integration/test_console_overlays.py
from __future__ import annotations

import pytest

from intui.console import build_console
from intui.events import MemorySource, read_recording


@pytest.mark.asyncio
async def test_slash_opens_and_esc_closes_files_overlay(tmp_path):
    from intui.emit import run_recorder

    out = tmp_path / "run.jsonl"
    rec = run_recorder(out, run_id="t")
    rec.run_started(summary="run")
    rec.file_changed("src/a.py")  # confirm the recorder method name in intui.emit
    rec.run_completed(status="passed")
    rec.close()

    app = build_console(MemorySource(list(read_recording(out))))
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("f")  # open files overlay
        await pilot.pause()
        assert app.screen_stack[-1].__class__.__name__ == "PanelOverlay"
        await pilot.press("escape")
        await pilot.pause()
        assert app.screen_stack[-1].__class__.__name__ != "PanelOverlay"
```

Note: confirm `MemorySource`, `run_test`, and the emit method that produces a file entry (used by `FileTree`) against `examples/` and `tests/integration/test_console_app.py`. If there's no `file_changed`, use whatever the file-tree fixture in the existing console test uses.

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/integration/test_console_overlays.py -v`
Expected: FAIL — `PanelOverlay` never pushed (assertion error or ImportError).

- [ ] **Step 3: Implement the overlay screen**

```python
# src/intui/console/overlays.py
"""Modal panel overlays: a browsable panel over the timeline, Esc to close."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widget import Widget


class PanelOverlay(ModalScreen[None]):
    DEFAULT_CSS = """
    PanelOverlay { align: center middle; }
    PanelOverlay > #overlay-frame {
        width: 80%; height: 80%;
        border: round $accent; padding: 1 2; background: $surface;
    }
    """
    BINDINGS = [("escape", "dismiss", "Close")]

    def __init__(self, title: str, panel: Widget) -> None:
        super().__init__()
        self._title = title
        self._panel = panel

    def compose(self) -> ComposeResult:
        frame = Vertical(self._panel, id="overlay-frame")
        frame.border_title = self._title
        yield frame

    def action_dismiss(self, result: None = None) -> None:
        self.dismiss(None)
```

- [ ] **Step 4: Wire `action_open_panel` + keys into `ConsoleApp`**

In `src/intui/console/app.py`, add to `BINDINGS` (replacing the old view keys):

```python
        ("t", "open_panel('tasks')", "Tasks"),
        ("l", "open_panel('lanes')", "Lanes"),
        ("f", "open_panel('files')", "Files"),
        ("e", "open_panel('evidence')", "Evidence"),
        ("m", "open_panel('metrics')", "Metrics"),
```

Add the action method:

```python
    def action_open_panel(self, name: str) -> None:
        from intui.console.overlays import PanelOverlay

        panel = self._panel_for(name)
        if panel is None:
            return
        self.push_screen(PanelOverlay(name, panel))

    def _panel_for(self, name: str):
        ps = self._public_safe
        if name == "files":
            return FileTree(file_tree_view(public_safe=ps))
        if name == "metrics":
            return MetricsPanel(metrics_view(public_safe=ps))
        if name == "lanes":
            return LanesPanel(lanes_view())
        if name == "evidence":
            return EvidencePanel(evidence_view(public_safe=ps))
        if name == "tasks":
            from textual.containers import VerticalScroll

            return VerticalScroll(
                TaskCounterChip(chip_view()),
                TaskTree(tree_view()),
            )
        return None
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `uv run pytest tests/integration/test_console_overlays.py -v`
Expected: PASS (1 passed).

- [ ] **Step 6: Gate + commit**

```bash
uv run pytest && uv run ruff check && uv run ruff format --check && uv run mypy
git add src/intui/console/overlays.py src/intui/console/app.py tests/integration/test_console_overlays.py
git commit -m "feat: panel overlays via slash keys, Esc to close (020)

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

## Task 5: Inline diff expansion (diff opens where the failure is)

The `d` key (and selecting a failure row) reveals the `DiffViewer` inline below the timeline instead of in a separate view — the approved "C for diffs" behavior.

**Files:**
- Modify: `src/intui/console/app.py` (mount a collapsible `DiffViewer` region in `compose`; toggle it)
- Test: `tests/integration/test_console_inline_diff.py`

**Interfaces:**
- Consumes: `DiffViewer(diff_view(public_safe=...))`.
- Produces: `ConsoleApp.action_toggle_diff()` — shows/hides a `#inline-diff` region; bound to `d`. When shown, the `DiffViewer` is mounted (or `display=True`) directly under `RunTimeline`.

- [ ] **Step 1: Write the failing test**

```python
# tests/integration/test_console_inline_diff.py
from __future__ import annotations

import pytest

from intui.console import build_console
from intui.events import MemorySource, read_recording


@pytest.mark.asyncio
async def test_d_toggles_inline_diff(tmp_path):
    from intui.emit import run_recorder

    out = tmp_path / "run.jsonl"
    rec = run_recorder(out, run_id="t")
    rec.run_started(summary="run")
    rec.diff_ready(path="src/a.py", unified="--- a\n+++ b\n@@\n-x\n+y\n")  # confirm signature
    rec.run_completed(status="passed")
    rec.close()

    app = build_console(MemorySource(list(read_recording(out))))
    async with app.run_test() as pilot:
        await pilot.pause()
        diff = app.query_one("#inline-diff")
        assert diff.display is False
        await pilot.press("d")
        await pilot.pause()
        assert diff.display is True
        await pilot.press("d")
        await pilot.pause()
        assert diff.display is False
```

Note: confirm the recorder's diff method (`diff_ready`) and its params against `src/intui/emit/` and the diff fixture used in `tests/integration/test_console_app.py`.

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/integration/test_console_inline_diff.py -v`
Expected: FAIL — no `#inline-diff` widget.

- [ ] **Step 3: Mount the inline region + toggle action**

This is folded into the `compose` rewrite in Task 6; for this task, add the region and action so the test passes. In `compose` (before `Footer`), add:

```python
        diff_region = DiffViewer(diff_view(public_safe=self._public_safe), id="inline-diff")
        diff_region.display = False
        yield diff_region
```

Add the binding `("d", "toggle_diff", "Diff")` and:

```python
    def action_toggle_diff(self) -> None:
        region = self.query_one("#inline-diff")
        region.display = not region.display
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/integration/test_console_inline_diff.py -v`
Expected: PASS (1 passed).

- [ ] **Step 5: Gate + commit**

```bash
uv run pytest && uv run ruff check && uv run ruff format --check && uv run mypy
git add src/intui/console/app.py tests/integration/test_console_inline_diff.py
git commit -m "feat: inline diff region toggled with d (020)

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

## Task 6: Rewire `ConsoleApp.compose` to the new single-column layout

Replace `Header → ActivityStrip → Horizontal[conversation | ViewRouter] → scrub-bar → CommandBar → Footer` with `Header → activity row (Signal + label) → RunTimeline (1fr) → inline-diff → SlashPalette/PromptInput → scrub-bar → Footer`. Update the existing integration test to the new structure.

**Files:**
- Modify: `src/intui/console/app.py` (`compose`, CSS, imports; drop `ViewRouter`/`ConversationLog` usage and the `view_slice`/`view_router_view` wiring in `build_console`)
- Modify: `tests/integration/test_console_app.py` (assert timeline + overlay behavior instead of `ViewRouter` id switches)

**Interfaces:**
- Consumes: `RunTimeline` (Task 2), `run_timeline_view` (Task 1), `activity_label_view` + `CONSOLE_SIGNAL_STYLES` (Task 3), `PanelOverlay`/`action_open_panel` (Task 4), inline diff (Task 5).
- Produces: the final composed `ConsoleApp`. `build_console` no longer needs `views=view_slice(...)`; keep the other slices.

- [ ] **Step 1: Update the integration test first (it should fail against old compose)**

In `tests/integration/test_console_app.py`, replace ViewRouter-id assertions with:

```python
        # timeline is the primary surface and reduced the run
        tl = app.query_one("intui.console.timeline_widget.RunTimeline")  # or by type import
        assert tl.log_text().strip()
        # a browsable panel opens as an overlay
        await pilot.press("m")
        await pilot.pause()
        assert app.screen_stack[-1].__class__.__name__ == "PanelOverlay"
        await pilot.press("escape")
        await pilot.pause()
```

Prefer importing the class: `from intui.console.timeline_widget import RunTimeline` then `app.query_one(RunTimeline)`.

- [ ] **Step 2: Run it to verify it fails**

Run: `uv run pytest tests/integration/test_console_app.py -v`
Expected: FAIL — old layout has no `RunTimeline`.

- [ ] **Step 3: Rewrite `compose` + CSS**

```python
    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="activity-row"):
            yield ActivityStrip(
                _activity_state,
                styles=CONSOLE_SIGNAL_STYLES,
                swoosh_glow=6,
                sweep_seconds=self._sweep_seconds,
            )
            yield Static(id="activity-label")
        yield RunTimeline(run_timeline_view())
        diff_region = DiffViewer(diff_view(public_safe=self._public_safe), id="inline-diff")
        diff_region.display = False
        yield diff_region
        yield PromptInput()  # confirm PromptInput's constructor in intui.kit
        yield Static(id="scrub-bar")
        yield Footer()
```

Update CSS:

```python
    CSS = """
    #activity-row { height: 1; background: $panel; }
    ActivityStrip { width: 1fr; padding: 0 1; }
    #activity-label { width: auto; padding: 0 1; color: $text-muted; }
    RunTimeline { height: 1fr; }
    #inline-diff { height: auto; max-height: 40%; border-top: solid $panel; }
    PromptInput { dock: bottom; height: auto; }
    #scrub-bar { dock: bottom; height: 1; padding: 0 1; color: $text-muted; }
    """
```

Add imports for `RunTimeline`, `run_timeline_view`, `CONSOLE_SIGNAL_STYLES`, `activity_label_view`, `PromptInput`; remove `ConversationLog`, `ViewRouter`, `TaskCounterChip`/`TaskTree`/panel imports that are now only used inside `_panel_for` (keep those used there). In `on_mount`, subscribe the activity label:

```python
        self.store.subscribe(lambda snap: self._refresh_activity_label(snap))

    def _refresh_activity_label(self, snapshot) -> None:
        try:
            label = self.query_one("#activity-label", Static)
        except Exception:  # noqa: BLE001
            return
        label.update(activity_label_view()(snapshot))
```

In `build_console`, drop `views=view_slice(VIEWS, "tasks")` (and the now-unused `VIEWS`, `view_slice`, `view_router_view`, `view_selected` emit path — remove `select_view` handling from `handle_intent`). Keep conversation/taskboard/artifacts/workspace/metrics/run_status slices.

Confirm `PromptInput`'s constructor signature in `src/intui/kit/prompt_input.py`; if it needs a submit callback or selector, wire it to `handle_intent` (a submitted slash string → `action_open_panel`/`action_toggle_diff`). If `PromptInput` requires wiring beyond scope, mount a read-only `Static` prompt affordance for now and open a follow-up — but prefer the real `PromptInput`.

- [ ] **Step 4: Run the full suite**

Run: `uv run pytest -v`
Expected: PASS — the updated console test, timeline, overlays, inline diff, motion, and the layering guard all green.

- [ ] **Step 5: Gate + commit**

```bash
uv run pytest && uv run ruff check && uv run ruff format --check && uv run mypy
git add src/intui/console/app.py tests/integration/test_console_app.py
git commit -m "feat: single-column timeline layout, floor-pinned prompt (020)

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

## Task 7: Motion polish — failure flash + streaming row swoosh-in

Add the one-shot red flash when a failure row first appears and a subtle fade/slide as new rows arrive, honoring `MotionMode` (reduced-motion → no animation).

**Files:**
- Modify: `src/intui/console/timeline_widget.py` (animate on new failure rows)
- Test: `tests/unit/test_run_timeline_widget.py` (add a motion-mode guard test)

**Interfaces:**
- Consumes: `self.app.intui_theme` / motion mode (confirm how `IntuiApp` exposes reduced-motion; mirror how `Signal` reads `MotionMode`).
- Produces: `RunTimeline._flash_on_new_failure(prev_rows, new_rows)` — triggers a single Textual `styles.animate("opacity", ...)` (or a CSS class toggle) only when a new failure row appears and motion is enabled; a pure predicate `_has_new_failure(prev, new) -> bool` is unit-tested.

- [ ] **Step 1: Write the failing test**

```python
def test_detects_a_newly_arrived_failure_row():
    from intui.console.timeline_widget import RunTimeline
    from intui.kit.state import TimelineRow

    prev = (TimelineRow(0, "task", "✓", "completed", "ok", "completed", ""),)
    new = prev + (TimelineRow(1, "failure", "✗", "failed", "FAILED x", "failed", ""),)
    assert RunTimeline._has_new_failure(prev, new) is True
    assert RunTimeline._has_new_failure(new, new) is False
```

- [ ] **Step 2: Run it to verify it fails**

Run: `uv run pytest tests/unit/test_run_timeline_widget.py::test_detects_a_newly_arrived_failure_row -v`
Expected: FAIL — `_has_new_failure` undefined.

- [ ] **Step 3: Implement the predicate + wire the flash**

```python
    @staticmethod
    def _has_new_failure(prev, new) -> bool:
        prev_fail = sum(1 for r in prev if r.kind == "failure")
        new_fail = sum(1 for r in new if r.kind == "failure")
        return new_fail > prev_fail
```

In `sync_view`, before reassigning `self._view`:

```python
    def sync_view(self, vm: TimelineFeedView) -> None:
        if self._has_new_failure(self._view.rows, vm.rows):
            self._flash()
        self._view = vm
        self.query_one("#timeline-body", Static).update(self._build_text())
        self.query_one("#timeline-scroll", VerticalScroll).scroll_end(animate=False)

    def _flash(self) -> None:
        if not self._motion_enabled():
            return
        body = self.query_one("#timeline-body", Static)
        body.styles.background = "#3a1414"
        body.styles.animate("background", value="", duration=0.9)

    def _motion_enabled(self) -> bool:
        mode = getattr(self.app, "motion_mode", None)
        from intui.theming import MotionMode

        return mode is not MotionMode.STEADY  # confirm the reduced-motion sentinel on IntuiApp
```

Confirm how `IntuiApp`/theme exposes reduced-motion; if there's a dedicated flag, use it. If animating `background` to `""` is invalid in this Textual version, toggle a `.flash` CSS class and clear it via `set_timer`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/unit/test_run_timeline_widget.py -v`
Expected: PASS.

- [ ] **Step 5: Gate + commit**

```bash
uv run pytest && uv run ruff check && uv run ruff format --check && uv run mypy
git add src/intui/console/timeline_widget.py tests/unit/test_run_timeline_widget.py
git commit -m "feat: one-shot failure flash on the timeline, motion-aware (020)

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

## Task 8: Docs, layering guard, screenshot, version bump, merge

Refresh docs/screenshot to the new UX, confirm layering, bump the version, and merge.

**Files:**
- Modify: `src/intui/__init__.py` (`__version__` → `1.2.0`)
- Modify: `CHANGELOG.md` (Added: single-column console UX)
- Modify: `README.md` / `docs/README.md` (console description + regenerate `docs/media/console.svg`)
- Modify: `tests/unit/test_layering.py` if needed (the new `intui.console.*` modules import Textual — they must be in the rendering layer, NOT the engine-free set; the root-import guard must still hold)

- [ ] **Step 1: Confirm layering + full gate**

Run: `uv run pytest tests/unit/test_layering.py -v`
Expected: PASS — `import intui` still pulls in no Textual; `intui.kit.state.timeline_feed` is engine-free; `intui.console.*` is rendering-layer.

- [ ] **Step 2: Regenerate the console screenshot**

Run the existing screenshot generator used for `docs/media/console.svg` (see how `018-release-prep` T004 produced it) against the new layout. Verify the SVG shows the single-column timeline + floor prompt.

- [ ] **Step 3: Update docs + changelog + version**

Edit `README.md` console line and `docs/README.md` to describe the timeline/overlay/inline-diff UX; add a `CHANGELOG.md` entry under a new `1.2.0` heading; set `__version__ = "1.2.0"` in `src/intui/__init__.py`; run `uv sync --reinstall-package intui`.

- [ ] **Step 4: Full gate**

Run: `uv run pytest && uv run ruff check && uv run ruff format --check && uv run mypy && uv build`
Expected: all green; wheel builds.

- [ ] **Step 5: Commit + merge**

```bash
git add -A
git commit -m "docs: console UX redesign — docs, screenshot, 1.2.0 (020)

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
git checkout main
git merge --no-ff 020-console-ux-redesign -m "Merge 020-console-ux-redesign: single-column timeline console (1.2.0)"
```

Then update project memory (020 done; console UX redesigned to a single-column timeline).

---

## Self-Review

**Spec coverage:**
- Chat window → timeline: Tasks 1–2, 6. ✓
- Prompt pinned to floor: Task 6 (`PromptInput` docked bottom). ✓
- KITT swoosh = run state (color per phase): Task 3, wired in Task 6. ✓
- Glyph+label vocabulary: Tasks 1 (rows), 3 (activity label). ✓
- Failure callout + one-shot flash: Tasks 1 (failure kind/border via `_row_color`), 7 (flash). ✓
- Streaming rows swoosh-in: Task 7 (folded with flash; scroll_end + fade). ✓
- Panels: inline diffs + slash overlays: Tasks 5 (inline diff) + 4 (overlays). ✓
- "What stays as-is" (events/state/reducers/selectors, kit widgets reused): Tasks reuse existing factories; only `intui.console` + one engine-free `kit.state` selector added. ✓
- Layering/public-safe/motion-mode constraints: Global Constraints + Tasks 3, 7, 8. ✓
- Integration test updated (Principle VII): Task 6. ✓

**Placeholder scan:** Remaining "confirm the signature" notes are verification steps against named source files (not logic placeholders) — each names the exact file to check and the fallback. No "TODO"/"add error handling"/"write tests for the above" left.

**Type consistency:** `TimelineRow`/`TimelineFeedView`/`run_timeline_view` defined in Task 1 and consumed with identical names in Tasks 2, 7. `CONSOLE_SIGNAL_STYLES`/`activity_label_view` defined in Task 3, consumed in Task 6. `PanelOverlay`/`action_open_panel` defined in Task 4, consumed in Task 6. `#inline-diff`/`action_toggle_diff` defined in Task 5, consumed in Task 6. `_has_new_failure` defined and consumed in Task 7. Consistent.
