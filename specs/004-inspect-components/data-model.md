# Data Model: Inspect Components

**Feature**: `004-inspect-components` | **Date**: 2026-06-13

Engine-free, immutable dataclasses with value equality (the re-render contract).

## DiffLine

| Field | Type | Notes |
|-------|------|-------|
| `kind` | enum: `add | remove | context` | Malformed lines default to `context`. |
| `text` | str | Line content (without the leading marker). |
| `old_no` | int \| None | Source line number when known. |
| `new_no` | int \| None | Result line number when known. |

## FileDiff

| Field | Type | Notes |
|-------|------|-------|
| `path` | str | Display path (normalized separators; redacted in public-safe mode). |
| `raw_path` | str | Original path as supplied. |
| `added` | int | Count of `add` lines. |
| `removed` | int | Count of `remove` lines. |
| `lines` | tuple[DiffLine, ...] | Ordered; empty when `no_text_diff`. |
| `no_text_diff` | bool | True for binary/unparseable entries. |

## DiffArtifact

`id`, `title`, `files: tuple[FileDiff, ...]`, `public_safe: bool`.

## EvidenceMetric

| Field | Type | Notes |
|-------|------|-------|
| `key` | str | Stable metric id. |
| `label` | str | Human label. |
| `value` | str \| int \| float \| tuple[str, ...] | Scalar or list (e.g. failure categories, delivered files). |
| `status` | str \| None | Optional status meaning (e.g. `passed`/`failed`); presented with glyph+label. |
| `unsafe` | bool | Value redacted in public-safe mode. |

## EvidenceArtifact

`id`, `title`, `metrics: tuple[EvidenceMetric, ...]`, `public_safe: bool`.

## ArtifactStore (derived slice)

- `diff: DiffArtifact | None` — latest diff artifact
- `evidence: EvidenceArtifact | None` — latest evidence artifact
- latest-of-each-type-wins.

## Standard event mapping (FR-002)

| Event type | Effect |
|------------|--------|
| `diff_ready` | Parse payload into a DiffArtifact (from `files` or `unified` text); store as latest diff. `public_safe` from payload (default True). |
| `evidence_ready` | Build an EvidenceArtifact from payload `metrics`; store as latest evidence. `public_safe` from payload (default True). |
| anything else | State unchanged (foundation reducer contract). |

## Unified-diff parsing (FR-003)

`parse_unified_diff(text) -> tuple[FileDiff, ...]`:

- File headers `--- a/<path>` / `+++ b/<path>` start a new FileDiff (path from
  the `+++` side, stripped of `a/`,`b/` prefixes).
- Hunk headers `@@ -l,s +l,s @@` seed line numbers.
- Body lines: `+` → add, `-` → remove, leading space or other → context.
- A `Binary files … differ` line → a FileDiff with `no_text_diff=True`.
- Malformed/own lines never raise; counts derive from add/remove lines.

## Redaction (FR-011/012, Principle VI)

`redact(text) -> str` replaces, in place, with `‹redacted›`:

- absolute local paths: Windows `[A-Za-z]:\\…`, POSIX `/…` segments
- URLs, especially with embedded credentials (`scheme://user:pass@host`)
- token-like runs: `sk-…`, long high-entropy alphanumeric/`_`/`-` sequences

Field/metric `unsafe=True` → value fully replaced by the marker. Redaction is
substring-wise so an unsafe fragment inside a larger string is removed too.

## Selectors

```text
diff_view(slice="artifacts", *, public_safe=True) -> Selector[DiffView]
evidence_view(slice="artifacts", *, public_safe=True) -> Selector[EvidenceView]
```

- `DiffView`: ordered `DiffFileRow`s (path, added, removed, no_text_diff) +
  per-path `DiffBody` (rendered DiffLines). Paths/lines redacted when
  `public_safe`.
- `EvidenceView`: ordered `EvidenceRow`s (label, rendered value, status glyph/
  label, present flag). Values redacted when `public_safe`.
- Default `public_safe=True` (FR-013). Memoized per snapshot.

## Presentation rules

- Diff line: `+ added` (success token), `- removed` (failure token), `  ctx`
  (muted). Marker is the non-color counterpart (SC-004). Long lines truncated.
- File row: `path  (+added −removed)`; `no_text_diff` → `path  (no text diff)`.
- Evidence row: `label  value`; status metrics prefix a glyph+label; list
  values enumerate; absent → `n/a`.
- Empty states: no changed files → `no changes`; no evidence → `no evidence`.
- Redaction marker `‹redacted›` is itself color-neutral and unambiguous.
