# in-TUI-tion

A Python library for building rich, modern, first-class terminal user
interfaces — structured state in, beautiful live UI out.

Applications describe facts as an **append-only event stream**; the library
reduces them into **immutable state snapshots**, projects those into **view
models**, and renders them through **widgets that update themselves**. User
input flows back as **named intents** — the library never mutates your state.
Recordings replay deterministically, so every UI behavior is testable without
a terminal.

```text
app adapter -> event stream -> reducer/state store -> view models
    ^                                                      |
    +------ intents <- user input <- widgets <-------------+
```

## Layers

1. **Core library** (`intui.events/state/viewmodels/actions/theming`) —
   engine-free pipeline: envelopes, streams, reducers, snapshots, selectors,
   intents, themes. Imports no terminal engine (enforced by lint + test).
2. **Rendering layer** (`intui.widgets`, `intui.app`) — built on
   [Textual](https://textual.textualize.io/): bound widgets/containers,
   render-coalescing bridge, the Signal motion primitive, app shell with
   confirmation flow.
3. **Component kit** (`intui.kit`) — high-level, data-driven components: a
   task counter chip, a two-level task tree, parallel lanes, command surfaces
   (an always-visible command menu + a searchable command palette), inspect
   components (a diff viewer + an evidence panel, public-safe by default), a
   prompt input, a signature full-width activity strip, modes + a conversation
   surface, and a central view router that points the main pane at a chosen
   view — over a shared engine-free state model (`intui.kit.state`) with
   ready-made reductions, a command registry, a unified-diff parser, and a
   public-safety redactor.
4. **Examples** (`examples/`) — first-class runnable demos of every feature.

## Install

```sh
pip install in-tui-tion        # or: uv add in-tui-tion
```

Python 3.11+, a modern terminal, inline types (`py.typed`).

Render a console from any compliant stream with **zero code**:

```sh
intui watch run.jsonl          # replay a captured stream
intui watch -- my-agent --json # spawn a producer and watch it live
intui watch --adapter intentforge run.ndjson  # normalize an IntentForge run
```

## Quickstart

Two paths — full guide in **[docs/quickstart.md](docs/quickstart.md)**:

- **Stream-first** — emit JSON lines per the
  **[event-stream contract](docs/event-stream-contract.md)** and the kit renders
  them (validate with `intui.events.validate_stream`).
- **Build-in-code** — compose the kit yourself.

Run the examples from a checkout:

```sh
uv sync
uv run python -m examples.operator_console  # the flagship: modes + whole kit
uv run python -m examples.mission_control   # the component kit demo
uv run python -m examples.hello_replay      # the foundation demo
uv run pytest                               # headless test suite
```

The **operator console** is the flagship — an agentic workbench with
Plan/Build/Inspect/Review modes, a conversation surface, a live prompt you can
type into, and the signature full-width KITT activity strip, composing every
kit component over one recorded run. See
[examples/operator_console/README.md](examples/operator_console/README.md).

The canonical event vocabulary every producer targets lives in
**[docs/event-stream-contract.md](docs/event-stream-contract.md)** (single
source of truth).

## Project governance

Spec-driven (GitHub Spec Kit): specs, plans, and tasks live under `specs/`;
principles live in [.specify/memory/constitution.md](.specify/memory/constitution.md).
