# Specification Quality Checklist: Zero-Config Console Runner

**Feature**: `009-console-runner`

**Purpose**: Validate spec completeness and quality before planning.

## Content Quality

- [x] No implementation details (languages, frameworks, APIs) drive the
      requirements — names like `ConsoleApp`/`watch`/`intui watch` are the
      product surface (the deliverable), not internal mechanics.
- [x] Focused on user value (zero-code console from a stream) and the toothbrush
      north star.
- [x] Written for the library's consumers (people who have a stream and want a
      console).
- [x] All mandatory sections completed.

## Requirement Completeness

- [x] No `[NEEDS CLARIFICATION]` markers remain.
- [x] Requirements are testable (each FR maps to a headless or Pilot test).
- [x] Success criteria are measurable (one command / zero code, live reduction,
      unwrapping, public-safe toggle, clear errors, clean-install launch).
- [x] Success criteria are technology-agnostic outcomes (a console renders, state
      reduces, errors are clear).
- [x] All acceptance scenarios are defined (file replay, live subprocess,
      defaults/public-safe/discoverability).
- [x] Edge cases identified (unknown-only stream, missing file, uncstartable
      command, empty live stream, large stream, tiny terminal, no-stdin-TTY).
- [x] Scope is bounded — consumes the **canonical** vocabulary; the IntentForge
      adapter and `--follow`/process controls are explicitly out of scope.
- [x] Dependencies/assumptions identified (depends on 002/004/005/006/007/008;
      subprocess-not-stdin; read-mostly default).

## Feature Readiness

- [x] All functional requirements have clear acceptance criteria.
- [x] User scenarios cover primary flows (replay, live, defaults).
- [x] Aligned with the constitution (engine-free sources + Pilot-tested app,
      public-safe by default, keyboard-first, example-driven, installable entry
      point).
- [x] No implementation leakage that pre-commits an internal design.

## Notes

- This is the "toothbrush" feature: the success bar is *zero application code*
  for a working console, so SC-001 (one command, zero code) is the headline.
- The boundary with feature 010 (IF adapter) is firm: this runner speaks the
  canonical vocabulary only; producer-specific normalization is the next feature.
