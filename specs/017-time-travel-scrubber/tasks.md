# Tasks: Time-Travel Scrubber

**Feature**: `017-time-travel-scrubber` | **Input**: plan.md, research.md,
data-model.md, contracts/contract-api.md

Test-first throughout (Principle VII). `[P]` = parallelizable. Gate after each
phase: `uv run pytest && uv run ruff check && uv run mypy`.

## Phase 1 — Store.snapshot_at (reconstruction)

- [ ] **T001** [P] Write `tests/unit/test_snapshot_at.py`: ingest a known event
      sequence into a store; assert `snapshot_at(k)` slice equals reducing exactly
      the first k events for several k (0, mid, len); `snapshot_at(len)` matches
      the live snapshot's reduced slice; out-of-range clamps; a reducer that
      raises on one event → that event is skipped (state matches live, no raise);
      calling `snapshot_at` does not change `store.snapshot`.
- [ ] **T002** Add `snapshot_at(index)` to `src/intui/state/store.py` (fold the
      reducer over `events[:n]` from `initial()`, try/except per event, attach
      health; clamp). Make T001 pass.

## Phase 2 — Timeline controller (engine-free)

- [ ] **T003** [P] Write `tests/unit/test_timeline.py`: default is live;
      `position(total)==total` when live; `pause(total)` freezes at total; `step`
      clamps to [0,total]; `to_start`→0; `to_end`/`resume`→live; `toggle` flips;
      immutability (ops return new); `label` reflects mode/position.
- [ ] **T004** Implement `src/intui/state/timeline.py` (`Timeline`) and export
      from `src/intui/state/__init__.py` (+ `__all__`). Make T003 pass.

## Phase 3 — Bridge hold / release

- [ ] **T005** [P] Write `tests/snapshot/test_bridge_hold.py` (Pilot or unit with
      a fake app): a bound widget renders a held snapshot; while held, a new store
      publish does not change the rendered view but updates the tracked latest;
      `release()` renders the latest.
- [ ] **T006** Add `hold(snapshot)` / `release()` + held-target rendering to
      `src/intui/widgets/bridge.py`. Make T005 pass.

## Phase 4 — Console scrubber

- [ ] **T007** [P] Extend `tests/integration/test_console_app.py` (Pilot): with a
      multi-event stream, pause (`space`) then step back (`,`) → a panel reflects
      the earlier state and the scrub bar shows the position; `home` → initial
      state; `end` → latest; with a still-live source, pause and assert the held
      view is fixed while the scrub-bar total grows, then resume shows latest.
- [ ] **T008** Wire the scrubber into `src/intui/console/app.py`: a `Timeline`
      field, scrub BINDINGS (`space`/`,`/`.`/`home`/`end`) + actions, a
      `#scrub-bar` Static, `_apply_scrub()` (hold/release + label), and a store
      subscription refreshing the bar. Make T007 pass.

## Phase 5 — Docs, gate, verify, merge

- [ ] **T009** [P] Docs: scrub keys in `docs/quickstart.md` + `README.md`; link
      the feature quickstart.
- [ ] **T010** Confirm layering: `snapshot_at` + `Timeline` engine-free
      (`test_layering.py` walks `intui.state`).
- [ ] **T011** Full gate: `uv run pytest && uv run ruff check && uv run mypy`;
      bump `src/intui/__init__.py` `__version__` to `0.17.0`.
- [ ] **T012** Fresh-build verify: `uv build` + clean-install; spot-check
      `store.snapshot_at` + `from intui.state import Timeline`.
- [ ] **T013** Merge: `git merge --no-ff` `017-time-travel-scrubber` into `main`;
      update project memory (017 done; road-to-1.0 → #4 release-prep pass → PyPI).

## Dependencies

- T002 ← T001; T004 ← T003; T006 ← T005. T008 ← T002+T004+T006; T007 first.
- T009–T013 last, in order.

## Parallelizable

`[P]`: T001, T003, T005, T007, T009 — distinct files.
