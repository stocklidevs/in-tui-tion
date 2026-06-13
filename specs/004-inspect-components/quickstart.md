# Quickstart: Inspect Components

**Feature**: `004-inspect-components` | **Date**: 2026-06-13

## Run the example

```sh
uv sync
uv run python -m examples.mission_control
```

Open the diff viewer and evidence panel (keys shown in the command menu).
The diff viewer lists changed files — select one to see its green/red diff.
The evidence panel shows the run's outcome metrics. Both render public-safe by
default (absolute paths and secrets redacted).

## Use the inspect components

```python
from intui.kit import DiffViewer, EvidencePanel
from intui.kit.state import artifacts_slice, diff_view, evidence_view
from intui.state import Store, compose_reducers

store = Store(compose_reducers(artifacts=artifacts_slice()))

class MyApp(IntuiApp):
    def compose(self):
        yield DiffViewer(diff_view())          # public-safe by default
        yield EvidencePanel(evidence_view())
```

Emit `diff_ready` (with `unified` text or structured `files`) and
`evidence_ready` (with a `metrics` list); the kit reduces them with no custom
reducers. For a trusted local context, pass `public_safe=False` to the
selector to show full values.

## Parse / redact directly

```python
from intui.kit.state import parse_unified_diff, redact

files = parse_unified_diff(open("change.patch").read())
safe = redact("see C:\\Users\\me\\secret and token sk-abc123")  # -> redacted markers
```

## Test headlessly

```sh
uv run pytest tests/unit -k "diff or evidence or redact"
uv run pytest tests/snapshot -k "diff or evidence"
```
