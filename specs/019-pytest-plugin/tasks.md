# Tasks: pytest Plugin

**Feature**: `019-pytest-plugin` | **Input**: plan.md, research.md,
data-model.md, contracts/contract-api.md

Test-first throughout (Principle VII). `[P]` = parallelizable. Gate after each
phase: `uv run pytest && uv run ruff check && uv run mypy`.

## Phase 1 — Plugin + entry point

- [ ] **T001** [P] Write `tests/unit/test_pytest_plugin.py` (uses `pytester`,
      `runpytest_subprocess`): make a tiny suite (a pass, a fail, a skip across
      two modules), run with `--intui=<tmp>`; read the stream with
      `read_recording` + reduce through taskboard/artifacts/run_status; assert
      `run_started` first, a started/completed pair per test scoped to its
      module, statuses (passed/failed/skipped), a failure `message_added`, and a
      final `evidence_ready` (counts) + `run_completed` status `failed`. Also:
      WITHOUT `--intui` no file is written and exit code is unchanged.
- [ ] **T002** Implement `src/intui/pytest_plugin.py`: `pytest_addoption`
      (`--intui` nargs="?"), `pytest_configure` (open `run_recorder`, register
      `_IntuiReporter`; warn+disable on open failure), `_IntuiReporter`
      (sessionstart/logstart/logreport/logfinish/sessionfinish per data-model).
- [ ] **T003** Add `[project.entry-points.pytest11] intui =
      "intui.pytest_plugin"` to `pyproject.toml`; `uv sync` so the entry point is
      active. Make T001 pass.

## Phase 2 — Example + docs

- [ ] **T004** [P] Add `examples/pytest_console/` — a small `test_sample.py`
      (pass/fail/skip) + `README.md` showing `pytest --intui=run.jsonl` then
      `intui watch run.jsonl` / `--follow`.
- [ ] **T005** [P] Docs: a "watch your tests" line in `docs/quickstart.md`, a
      feature-tour row in `README.md`, and a link in `docs/README.md`; link the
      feature quickstart.

## Phase 3 — Gate, verify, release

- [ ] **T006** Confirm engine-free/layering: `intui` root import does not load
      `pytest`/the plugin (existing `test_layering.py` root-import guard);
      plugin imports only `pytest` + `intui.emit`.
- [ ] **T007** Full gate: `uv run pytest && uv run ruff check && uv run ruff
      format --check && uv run mypy`; bump `__version__` to `1.1.0`;
      update `CHANGELOG.md` (Added: pytest plugin).
- [ ] **T008** Fresh-build verify: `uv build` + `twine check`; clean-install the
      wheel; in a temp project run `pytest --intui=<tmp>` and confirm the stream
      reduces (entry point active from the installed wheel).
- [ ] **T009** Merge: `git merge --no-ff` `019-pytest-plugin` into `main`; tag if
      releasing; update project memory (019 done; first producer integration).

## Dependencies

- T002 ← T001; T003 ← T002. T004/T005 after T002. T006–T009 last, in order.

## Parallelizable

`[P]`: T001, T004, T005 — distinct files.

## Note (release)

This is a new feature → **minor** bump to `1.1.0`. Publishing to PyPI is the
same gated flow as 1.0.0 (draft a GitHub Release on the new tag → Trusted
Publishing) — do it when you're ready, not automatically.
