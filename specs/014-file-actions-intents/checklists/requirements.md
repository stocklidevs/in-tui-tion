# Specification Quality Checklist: File Actions as Intents

**Feature**: `014-file-actions-intents`

## Content Quality

- [x] No implementation details drive the requirements (the *what*: act on files
      via intents; not how the editor is launched).
- [x] Focused on user value (act on produced files) while keeping the boundary.
- [x] Written for consumers (app authors) and end users (tree actions).
- [x] All mandatory sections completed.

## Requirement Completeness

- [x] No `[NEEDS CLARIFICATION]` markers remain.
- [x] Requirements are testable (each FR → headless or Pilot test).
- [x] Success criteria measurable (intents delivered with path, delete confirmed,
      helpers act, console opt-in fulfills/doesn't, engine-free).
- [x] Success criteria technology-agnostic outcomes.
- [x] Acceptance scenarios defined (intent delivery, confirmed delete, wiring).
- [x] Edge cases identified (no selection, directory, cancel, no $EDITOR, helper
      errors, viewer never mutates by default).
- [x] Scope bounded — files only; download deferred; intents not added to the
      event vocabulary; library never mutates.
- [x] Dependencies/assumptions identified (builds on FileTree 013, intent +
      confirmation 001/003, ConsoleApp 009).

## Feature Readiness

- [x] All functional requirements have clear acceptance criteria.
- [x] User scenarios cover primary flows (act, confirmed delete, wire real).
- [x] Aligned with the constitution (Principle III — library never mutates;
      intents + confirmation; engine-free helpers; keyboard-first; public-safe).
- [x] No implementation leakage that pre-commits an internal design.

## Notes

- The crux: the library provides the affordance (intents + confirmation + reusable
  helpers); the application performs the side effect. Mutation in the generic
  console is opt-in (`file_actions=True`), never the default.
