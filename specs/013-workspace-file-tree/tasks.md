# Tasks: Workspace File Tree

**Feature**: `013-workspace-file-tree` | **Input**: plan.md, research.md,
data-model.md, contracts/contract-api.md

Test-first throughout (Principle VII). `[P]` = parallelizable. Gate after each
phase: `uv run pytest && uv run ruff check && uv run mypy`.

## Phase 1 — Workspace state + tree selector (engine-free)

- [ ] **T001** [P] Write `tests/unit/test_workspace.py`: reducer upserts files by
      normalized path (`\`→`/`, strip `./`); status added vs modified; repeat
      write updates in place; `file_removed` removes (unknown removal ignored);
      `file_tree_view` nests (`src/app.py`,`src/util.py`,`README.md` → `src` dir
      with two files + top-level README), dirs-before-files alpha order, empty
      dirs absent, removal prunes; public-safe redacts an absolute path, relative
      passes; `WORKSPACE_EVENT_TYPES ⊆ KNOWN_EVENT_TYPES`.
- [ ] **T002** Implement `src/intui/kit/state/workspace.py`: `WORKSPACE_EVENT_TYPES`,
      `FileEntry`, `WorkspaceState`, `workspace_slice()`, `FileNode`,
      `FileTreeView`, `file_tree_view()`; path normalization + nest/sort + redact.
- [ ] **T003** Export workspace names from `src/intui/kit/state/__init__.py`
      (+ `__all__`) and union `WORKSPACE_EVENT_TYPES` into `KNOWN_EVENT_TYPES`
      (update `tests/unit/test_vocabulary.py` module-set list). Make T001 pass.

## Phase 2 — scan_workspace (live convenience)

- [ ] **T004** [P] Extend `tests/unit/test_workspace.py`: `scan_workspace(tmp)`
      over a nested temp dir yields `file_written` events with **relative**
      normalized paths; feeding them through a store builds the matching tree.
- [ ] **T005** Implement `scan_workspace(root, *, run_id)` in `workspace.py`
      (stdlib `os.walk`/`pathlib`, relative paths). Make T004 pass.

## Phase 3 — FileTree widget (Pilot)

- [ ] **T006** [P] Write `tests/snapshot/test_file_tree.py` (Pilot): build a
      store with `workspace_slice`, ingest file events, mount `FileTree`,
      `app.run_test()`; assert it renders the dirs/files; navigate with the
      keyboard (expand/collapse); assert paths()/labels() introspection.
- [ ] **T007** Implement `src/intui/kit/file_tree.py`: `FileTree(BoundContainer)`
      over Textual `Tree`, recursive node build, dir/file glyph + status,
      expansion preserved by path; lazy-export from `src/intui/kit/__init__.py`.
      Make T006 pass.

## Phase 4 — SDK helpers + console "files" view

- [ ] **T008** [P] Extend `tests/unit/test_emit.py`: `rec.file_written(path,
      change_type=…)` / `rec.file_removed(path)` emit valid envelopes that reduce
      into the tree.
- [ ] **T009** Add `file_written`/`file_removed` to `src/intui/emit.py`.
- [ ] **T010** Wire the console: add `"files"` to `VIEWS`, a `workspace` slice in
      `build_console`, a `FileTree` pane, and `Command("view_files","Files",
      select_view_intent("files"),key="f")` in `src/intui/console/app.py`.
- [ ] **T011** Extend `tests/integration/test_console_app.py`: press `f` → the
      files view is current; a stream with `file_written` shows the tree.

## Phase 5 — Example, docs, gate, verify, merge

- [ ] **T012** [P] Update `examples/emit_demo/run.py` to emit `file_written` for
      the files it diffs (so the demo shows a tree); note `f` in its README.
- [ ] **T013** [P] Docs: add `file_written`/`file_removed` to
      `docs/event-stream-contract.md` (workspace section) and a "files" line to
      `docs/quickstart.md`; link the feature quickstart.
- [ ] **T014** Confirm layering: `workspace.py` (incl. `scan_workspace`) stays
      engine-free (it's under the `intui.kit.state` walk in `test_layering.py`).
- [ ] **T015** Full gate: `uv run pytest && uv run ruff check && uv run mypy`;
      bump `src/intui/__init__.py` `__version__` to `0.13.0`.
- [ ] **T016** Fresh-build verify: `uv build` + clean-install; spot-check
      `scan_workspace` + a `FileTree` reduce/render path imports and runs.
- [ ] **T017** Merge: `git merge --no-ff` `013-workspace-file-tree` into `main`;
      update project memory (013 done; generic file tree primitive shipped).

## Dependencies

- T002 ← T001; T003 ← T002. T005 ← T004 (+ T002). T007 ← T006 (+ T002/T003).
- T009 ← T008. T010 ← T007+T009; T011 ← T010.
- T012 ← T009; T013 anytime after code; T014–T017 last, in order.

## Parallelizable

`[P]`: T001, T004, T006, T008, T012, T013 — distinct files.
