# Tasks: File Actions as Intents

**Feature**: `014-file-actions-intents` | **Input**: plan.md, research.md,
data-model.md, contracts/contract-api.md

Test-first throughout (Principle VII). `[P]` = parallelizable. Gate after each
phase: `uv run pytest && uv run ruff check && uv run mypy`.

## Phase 1 — Intent helpers (engine-free)

- [ ] **T001** [P] Extend `tests/unit/test_workspace.py`: `open_file_intent`,
      `copy_path_intent`, `delete_file_intent` carry `{"path": …}`; `delete_file`
      is `risky=True`; names are `open_file`/`copy_path`/`delete_file`; these
      types are NOT in `KNOWN_EVENT_TYPES`.
- [ ] **T002** Implement the three helpers in `src/intui/kit/state/workspace.py`
      (import `Intent` from `intui.actions`); export from
      `src/intui/kit/state/__init__.py` (+ `__all__`). Make T001 pass.

## Phase 2 — Opt-in convenience helpers

- [ ] **T003** [P] Write `tests/unit/test_file_actions.py`: `delete_path(tmp)`
      removes a file; `save_copy(src, dst)` copies + returns dst; `open_in_editor`
      with an injected `run` and `editor="vi"` runs `["vi", path]`; with no editor
      env resolves a platform opener argv (assert non-empty argv via injected run);
      helpers raise on missing file / bad dest (caller handles).
- [ ] **T004** Implement `src/intui/actions/files.py` (`delete_path`, `save_copy`,
      `open_in_editor`; engine-free stdlib) and export from
      `src/intui/actions/__init__.py`. Make T003 pass.

## Phase 3 — FileTree affordances (Pilot)

- [ ] **T005** [P] Extend `tests/snapshot/test_file_tree.py`: with a recording
      `on_intent` handler, focus the tree, move the cursor to a file, press `o`/`c`
      → `open_file`/`copy_path` intents with the path delivered; press `x` →
      confirmation appears, confirm → `delete_file` delivered, cancel → nothing;
      cursor on a directory → action keys post nothing; `selected_file()` correct.
- [ ] **T006** Add `BINDINGS` (`o`/`c`/`x`) + action methods + `selected_file()`
      to `src/intui/kit/file_tree.py` (read `Tree.cursor_node`; files only via
      `allow_expand`; `self.app.post_intent(...)`). Make T005 pass.

## Phase 4 — Console integration

- [ ] **T007** [P] Extend `tests/integration/test_console_app.py`: default
      console — `copy_path` copies to clipboard (assert via a spy/`copy_to_
      clipboard`), `delete_file` does NOT remove a temp file (report-only);
      `build_console(file_actions=True)` — a confirmed `delete_file` removes the
      temp file and `open_file` invokes the opener (injected/spy).
- [ ] **T008** Add `file_actions` to `ConsoleApp`/`build_console` and the
      `copy_path`/`open_file`/`delete_file` branches to `ConsoleApp.handle_intent`
      in `src/intui/console/app.py`. Make T007 pass.

## Phase 5 — Docs, gate, verify, merge

- [ ] **T009** [P] Docs: note the file-action keys (`o`/`c`/`x`) + `file_actions`
      flag in `docs/quickstart.md`; link the feature quickstart; mention in the
      emit_demo README.
- [ ] **T010** Confirm layering: intent helpers + `intui.actions.files` stay
      engine-free (`test_layering.py` walks `intui.actions` + `intui.kit.state`).
- [ ] **T011** Full gate: `uv run pytest && uv run ruff check && uv run mypy`;
      bump `src/intui/__init__.py` `__version__` to `0.14.0`.
- [ ] **T012** Fresh-build verify: `uv build` + clean-install; spot-check
      `from intui.actions.files import delete_path` and the intent helpers import
      and work on a temp file.
- [ ] **T013** Merge: `git merge --no-ff` `014-file-actions-intents` into `main`;
      update project memory (014 done; file actions are intents, library never
      mutates).

## Dependencies

- T002 ← T001; T004 ← T003. T006 ← T002+T005. T008 ← T004+T006+T007.
- T009–T013 last, in order.

## Parallelizable

`[P]`: T001, T003, T005, T007, T009 — distinct files.
