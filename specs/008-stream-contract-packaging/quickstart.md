# Quickstart: Stream Contract & Packaging

**Feature**: `008-stream-contract-packaging` | **Date**: 2026-06-13

## Validate a stream against the contract

```python
from intui.events import validate_stream
from intui.kit.state import KNOWN_EVENT_TYPES

issues = validate_stream("run.jsonl", known_types=KNOWN_EVENT_TYPES)
for i in issues:
    print(f"line {i.line} [{i.severity}] {i.reason}")
```

Conforming streams report nothing; malformed envelopes report errors per line;
event types outside the canonical vocabulary report warnings (the runtime still
tolerates them).

## Install

```sh
uv build                       # builds the wheel
pip install dist/in_tui_tion-*.whl   # into a clean env
python -c "import intui; print(intui.__version__)"
```

The package ships inline types (`py.typed`), so type checkers see them.

## The two adoption paths (see docs/)

- **Stream-first** — emit the canonical JSON lines (see
  [docs/event-stream-contract.md](../../docs/event-stream-contract.md)) and a
  console renders them. (The zero-config runner is the next feature.)
- **Build-in-code** — compose the kit yourself; see
  [docs/quickstart.md](../../docs/quickstart.md) and the `examples/`.

## Test headlessly

```sh
uv run pytest tests/unit -k "validate or vocabulary or version"
```
