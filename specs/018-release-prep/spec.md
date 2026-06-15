# Feature Specification: Release Prep (1.0.0)

**Feature Branch**: `018-release-prep`

**Created**: 2026-06-14

**Status**: Draft

**Input**: Road-to-1.0 item 4 (final). All capability features are done
(008–017). Make the project a credible first public release: cohesive docs, a
changelog, a visual, polished packaging metadata, CI, version `1.0.0`, then push
to GitHub and publish to PyPI (the name `in-tui-tion` is confirmed available).

## Overview

This is the packaging/polish pass — no new runtime behavior. The docs have grown
feature-by-feature; this consolidates them into one story, adds the release
artifacts a public project needs, verifies the wheel end to end (incl. a TestPyPI
dry-run), tags `v1.0.0`, pushes the source to GitHub, and publishes to PyPI.

Two steps are **outward-facing** and gated on the maintainer: pushing the public
GitHub repo, and uploading to TestPyPI/PyPI (needs a token). Everything else is
prepared and verified locally first.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A newcomer understands and installs it (Priority: P1)

Someone lands on the README/PyPI page and, in one read, gets what in-TUI-tion is,
installs it, and runs a first console — without piecing it together from per-
feature notes.

**Why this priority**: The first impression decides adoption; the docs must read
as one coherent story for 1.0.

**Independent Test**: README renders top-to-bottom as a single narrative (what /
install / watch / emit / feature tour / examples / governance); `pip install
in-tui-tion` and `intui watch <file>` appear early; all internal doc links
resolve.

**Acceptance Scenarios**:

1. **Given** the README, **When** read start to finish, **Then** it presents the
   value, install, the watch + emit paths, a feature tour, examples, and links —
   no contradictions or stale "next feature" notes.
2. **Given** the `docs/` folder, **When** opened, **Then** an index links the
   quickstart, the contract, and the per-feature quickstarts.
3. **Given** a `CHANGELOG.md`, **When** read, **Then** it summarizes the path to
   1.0.0.

### User Story 2 - The package is publishable and trustworthy (Priority: P1)

The wheel builds, carries complete metadata (classifiers, URLs, keywords,
typing), installs cleanly from an index, and the repo links resolve.

**Why this priority**: A 1.0 on PyPI must look and behave like a real release.

**Independent Test**: `uv build` + `twine check` pass; metadata includes the
expected classifiers/URLs; a clean install from **TestPyPI** works and `intui`
runs; the `Repository` URL resolves to the pushed GitHub repo.

**Acceptance Scenarios**:

1. **Given** the built artifacts, **When** validated, **Then** `twine check`
   passes and the metadata has classifiers, keywords, `py.typed`, and project
   URLs (Homepage, Repository, Issues, Changelog, Documentation).
2. **Given** a TestPyPI upload, **When** installed into a clean env from
   TestPyPI, **Then** `from intui import run_recorder` and `intui --help` work.
3. **Given** `v1.0.0`, **When** tagged and pushed, **Then** the GitHub repo shows
   the source + tag and the PyPI links resolve to it.

### User Story 3 - Contributors can build and trust the repo (Priority: P2)

The public repo has CI that runs the gate (tests, lint, types) on push/PR, so
contributors and users see green status.

**Why this priority**: CI signals a maintained, trustworthy project.

**Independent Test**: A CI workflow runs `pytest`/`ruff`/`mypy` on push; it is
present and valid.

**Acceptance Scenarios**:

1. **Given** the repo, **When** code is pushed, **Then** CI runs the full gate.
2. **Given** the workflow, **When** inspected, **Then** it uses the project's
   tooling (uv + pytest/ruff/mypy) on supported Python versions.

### Edge Cases

- A doc link points at a moved/old path: caught and fixed (no 404s).
- The version is bumped but the editable metadata is stale: reinstall so
  `__version__` == distribution metadata (existing test).
- TestPyPI/PyPI name or token issues: surfaced at the gated upload step, not
  silently; the dry-run catches packaging problems before the real index.
- The GitHub repo doesn't exist yet / push auth missing: the push step pauses for
  the maintainer (outward-facing).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The README MUST read as one coherent narrative (value, install,
  watch + emit, feature tour, examples, governance) with no stale "next feature"
  text and all internal links resolving.
- **FR-002**: A `docs/` index MUST link the quickstart, the event-stream
  contract, and the per-feature quickstarts.
- **FR-003**: A `CHANGELOG.md` MUST summarize the releases up to `1.0.0`.
- **FR-004**: Packaging metadata MUST be release-grade: classifiers (incl.
  Development Status, Environment :: Console, Typing :: Typed, supported Python
  versions, License, Topic), `keywords`, and `project.urls` (Homepage,
  Repository, Issues, Changelog, Documentation).
- **FR-005**: A README **visual** (a real screenshot/SVG of the console) MUST be
  included and referenced.
- **FR-006**: A CI workflow MUST run the full gate (pytest + ruff + mypy) via uv.
- **FR-007**: The version MUST be `1.0.0`, with the full gate green and the wheel
  building + clean-installing; `twine check` MUST pass.
- **FR-008**: The source MUST be pushed to the GitHub repo named in the metadata
  (`stocklidevs/in-tui-tion`) with a `v1.0.0` tag (maintainer-gated step).
- **FR-009**: The package MUST be verified via a **TestPyPI** dry-run before the
  real PyPI publish; the real publish is a maintainer-gated step.

### Key Entities

- **README / docs index / CHANGELOG**: the consolidated documentation.
- **Packaging metadata**: classifiers, keywords, URLs in `pyproject.toml`.
- **CI workflow**: the gate on push/PR.
- **Release artifacts**: the `1.0.0` wheel/sdist, the `v1.0.0` tag.

## Success Criteria *(mandatory)*

- **SC-001**: README + `docs/` index read as one story; all internal links
  resolve; no stale roadmap text.
- **SC-002**: `CHANGELOG.md` covers up to 1.0.0.
- **SC-003**: `uv build` + `twine check` pass; metadata complete; clean install
  from TestPyPI runs `intui` and imports the SDK.
- **SC-004**: CI workflow present and runs the gate.
- **SC-005**: Version is `1.0.0`; full gate green; GitHub repo pushed with the
  `v1.0.0` tag (gated); PyPI publish authorized + done (gated).

## Assumptions

- Name `in-tui-tion` (import/CLI `intui`) is kept and is available on PyPI
  (verified 2026-06-14).
- Pushing the public GitHub repo and uploading to TestPyPI/PyPI are
  maintainer-gated (credentials/visibility); all local prep + the dry-run happen
  first.
- No new runtime code — this pass is docs, metadata, CI, verification, and
  release. (Research/data-model/contracts are N/A — no API surface added.)
- Post-1.0 backlog (textual serve, run comparison, graph views, session browser,
  adapter registry) is explicitly out of scope.
