# Research & Decisions: Producer SDK (emit)

**Feature**: `012-producer-sdk` | **Date**: 2026-06-14

## D1 — Reuse `Event`/`Scope` for construction; serialize via `to_mapping()`

**Decision**: The recorder builds `intui.events.Event` objects (with `Scope`) and
serializes with the existing `Event.to_mapping()` → `json.dumps`. It does not
re-implement the envelope.

**Why**: One source of truth for the envelope shape; whatever the pipeline parses
is exactly what the SDK emits (round-trip safe). Less code, no drift.

**Alternatives rejected**: hand-build dicts in the SDK — duplicates envelope
knowledge and risks drift from `parse_event`.

## D2 — Sinks: path | text file | callable | stdout (default)

**Decision**: `run_recorder(sink=None)` accepts a `Path`/`str` (opened for
append/write, newline="\n"), a text file object, a callable
`(Mapping[str,Any]) -> None`, or `None` → stdout. File/stdout sinks write one
`json.dumps(envelope)` line and flush; a callable sink receives the envelope
mapping directly (great for tests / custom routing).

**Why**: Covers the three real cases — capture to a file, stream live to stdout
(the `intui watch -- <tool>` path), and programmatic capture. Flush-per-line is
required so a live consumer sees events immediately (FR-003).

**Alternatives rejected**: file-only — loses the live story; a bespoke sink
protocol/class — heavier than a callable for no gain.

## D3 — Deterministic ids (counter); injectable clock

**Decision**: `event_id` is a per-recorder monotonic counter (`e1`, `e2`, …);
`timestamp` defaults to `datetime.now(UTC)` but a `clock: () -> datetime` is
injectable. `run_id` defaults to a generated id (`run-<short>`), overridable.

**Why**: Counters are unique, ordered, and deterministic (good recordings/tests);
an injectable clock makes emit fully deterministic under test while keeping real
wall-clock timestamps in production. Matches the adapter's determinism stance
(010 D2/D3).

**Alternatives rejected**: UUID ids — non-deterministic, noisier; mandatory
explicit timestamps — burdens every call.

## D4 — Bare canonical envelopes (no wrapper)

**Decision**: The SDK emits **bare** envelopes (the contract), not a
`{"type":"run_trace_event","event":…}` wrapper.

**Why**: `intui watch` reads bare envelopes directly (no `--adapter` needed),
which is the whole point — the SDK and the runner speak the same canonical
language. Wrappers are a producer-specific quirk the adapter layer exists to
absorb (010); a first-party SDK shouldn't need one.

**Alternatives rejected**: wrap like IntentForge — pointless indirection for our
own emitter.

## D5 — Context-manager handles for lifecycle

**Decision**: `run()`, `task(id, title?)`, and `Task.work_item(id, …)` are
context managers: emit the started event on `__enter__`, the completed event on
`__exit__` with `status` defaulting to completed, or `failed`/`run_failed` when
the block raises (then re-raise). Work items created off a `Task` carry that
task's id in scope (nest under it).

**Why**: Removes start/finish bookkeeping and makes the correct thing automatic,
including recording failures — the common case becomes a `with` block. Nesting
via the handle gives the tree structure for free (works with 011's nesting).

**Alternatives rejected**: only flat methods — correct but verbose and easy to
forget the completion; decorator-only — less flexible than a `with` block.

## D6 — `diff()` builds unified text via stdlib `difflib`

**Decision**: `diff(path, *, before, after, public_safe=True)` computes
`difflib.unified_diff(before.splitlines(keepends=True), after…, fromfile=a/path,
tofile=b/path)` and emits `diff_ready` with that `unified` text; `diff_unified`
accepts pre-built text. Multiple `diff(...)` calls accumulate (011).

**Why**: Mirrors exactly how IntentForge builds diffs (`build_file_diff`), so the
kit's `parse_unified_diff` consumes it unchanged; one-liner for the most common
artifact. stdlib only.

**Alternatives rejected**: a structured `files` payload builder — more API
surface; unified text is the lingua franca the kit already parses and what real
producers emit.

## D7 — Re-export from the engine-free root

**Decision**: export `run_recorder`/`RunRecorder` from `intui/__init__.py` so
`from intui import run_recorder` works.

**Why**: Maximum ergonomics for the headline use case; `intui.emit` is
engine-free (stdlib + `intui.events`), so the root stays Textual-free and the
layering guard holds.

**Alternatives rejected**: only `from intui.emit import …` — an extra hop for the
single most important on-ramp.

## D8 — SDK does not redact

**Decision**: the SDK emits exactly what the producer passes; it does not redact.
`public_safe` flags on `diff`/`evidence` are passed through to the payload.

**Why**: Producers own their data and context; redaction is a *display* concern
the console applies by default (Principle VI, feature 004). Redacting at emit
time would lose information irreversibly and duplicate the consumer's job.

**Alternatives rejected**: redact-on-emit — irreversible, wrong layer.

## Open questions / deferred

- **Non-Python emitters**: the contract is language-agnostic JSON; other-language
  SDKs can follow — out of scope here.
- **Declarative console *builder*** (consume-side ergonomics): separate future
  slice; this feature is the produce side.
- **Async/threaded emit**: keep sync now; revisit if a real need appears.
