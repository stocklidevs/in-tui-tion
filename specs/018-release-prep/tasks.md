# Tasks: Release Prep (1.0.0)

**Feature**: `018-release-prep` | **Input**: spec.md

Road-to-1.0 item 4 (final). No new runtime code — docs, metadata, CI,
verification, release. Local prep first; outward-facing steps gated last.

## Phase 1 — Documentation cohesion

- [x] **T001** Rewrite `README.md` as one narrative: tagline + value; install;
      the two paths (watch a stream / emit with the SDK); a concise **feature
      tour** (runner, IF adapter, rich diffs, file tree + actions, metrics,
      follow/record, time-travel scrubber); examples; governance. Remove any
      stale "next feature" text.
- [x] **T002** [P] Add `docs/README.md` (index) linking the quickstart, the
      event-stream contract, and the per-feature quickstarts (009–017).
- [x] **T003** [P] Add `CHANGELOG.md` (Keep-a-Changelog style) summarizing the
      path to **1.0.0** (highlights per feature area).
- [x] **T004** [P] Generate a real console screenshot SVG into
      `docs/media/console.svg` and reference it near the top of the README.

## Phase 2 — Packaging metadata

- [x] **T005** Polish `pyproject.toml`: `keywords`, a full `classifiers` set
      (Development Status :: 5 - Production/Stable, Environment :: Console,
      Intended Audience, Topic :: Software Development, Topic :: Terminals,
      Programming Language :: Python 3.11/3.12/3.13, License, Typing :: Typed),
      and `project.urls` (Homepage, Repository, Issues, Changelog, Documentation).
- [x] **T006** Verify the wheel includes `py.typed` + the README renders as the
      long description (content-type markdown). `uv build` then `twine check dist/*`.

## Phase 3 — CI

- [x] **T007** [P] Add `.github/workflows/ci.yml`: on push/PR, set up uv, run
      `uv run pytest`, `uv run ruff check`, `uv run ruff format --check`,
      `uv run mypy` on Python 3.11–3.13 (extras incl. `[metrics]`/dev).

## Phase 4 — Version + final gate

- [x] **T008** Bump `src/intui/__init__.py` `__version__` to `1.0.0`; `uv sync
      --reinstall-package in-tui-tion`.
- [x] **T009** Full gate green: `uv run pytest && uv run ruff check && uv run
      ruff format --check && uv run mypy`; `uv build`; `twine check dist/*`;
      clean-install the wheel (with `[metrics]`) and smoke-test `intui --help` +
      `from intui import run_recorder`.

## Phase 5 — Release (commit, merge, GitHub, PyPI) — outward-facing gated

- [x] **T010** Commit + `git merge --no-ff` `018-release-prep` into `main`.
- [x] **T011** Tag `v1.0.0` on `main`.
- [ ] **T012** **[GATED]** Create/confirm the GitHub repo
      `stocklidevs/in-tui-tion`; `git remote add origin …`; push `main` + tags.
      (Maintainer creates the repo / supplies push auth.)
- [ ] **T013** **[GATED]** TestPyPI dry-run: `uv publish --publish-url
      https://test.pypi.org/legacy/ …` (token), then clean-install from TestPyPI
      and smoke-test.
- [ ] **T014** **[GATED]** Publish to PyPI (token); verify `pip install
      in-tui-tion` from the real index.
- [ ] **T015** Update project memory (1.0.0 released; record name + repo + the
      post-1.0 backlog).

## Dependencies

- T001–T004 any order; T005–T006 after; T007 independent. T008→T009 after docs +
  metadata. T010 after T009. T011 after T010. T012–T014 gated, in order;
  T015 last.

## Parallelizable

`[P]`: T002, T003, T004, T007 — distinct files.

## Gated steps

T012 (GitHub push — public), T013/T014 (TestPyPI/PyPI upload — token). Prepare
and dry-run everything; pause for maintainer authorization on these.
