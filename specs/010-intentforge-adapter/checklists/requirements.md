# Specification Quality Checklist: IntentForge Adapter

**Feature**: `010-intentforge-adapter`

**Purpose**: Validate spec completeness and quality before planning.

## Content Quality

- [x] No implementation details drive the requirements — `adapt_record`/
      `IntentForgeSource`/`--adapter intentforge` are the deliverable surface.
- [x] Focused on user value: a real IF run becomes a console with one switch.
- [x] Written for consumers (people running IntentForge who want a console).
- [x] All mandatory sections completed.

## Requirement Completeness

- [x] No `[NEEDS CLARIFICATION]` markers remain.
- [x] Requirements are testable (each FR maps to a headless or Pilot test).
- [x] Success criteria are measurable (one command, per-event mapping, live
      reduction, summary→evidence, zero envelope errors, no crash on edge cases).
- [x] Success criteria are technology-agnostic outcomes.
- [x] All acceptance scenarios are defined (captured replay, live subprocess,
      Python reuse).
- [x] Edge cases identified (empty/missing diff, unknown name, malformed line,
      no timestamp, varying summary, case_id-as-work-item-id quirk).
- [x] Scope bounded — only the adapter + CLI switch + example; the kit/contract
      are unchanged.
- [x] Dependencies/assumptions identified (depends on 009 sources + canonical
      contract; IF shapes verified 2026-06-14; loose coupling, no IF import).

## Feature Readiness

- [x] All functional requirements have clear acceptance criteria.
- [x] User scenarios cover primary flows (replay, live, code reuse).
- [x] Aligned with the constitution (engine-free pure adapter + source, Pilot
      example, public-safe preserved, example-driven).
- [x] No implementation leakage that pre-commits an internal design.

## Notes

- The mapping table is the heart of the spec and is verified against the IF repo
  (run_trace.py / assembly_executor.py / assembly_benchmark.py / file_diff.py /
  cli.py) as of 2026-06-14.
- This closes the strategy loop: canonical contract (008) → zero-config runner
  (009) → IF adapter (010) = "point it at a real IF run, get a console."
