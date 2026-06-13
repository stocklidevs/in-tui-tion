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
   (an always-visible command menu + a searchable command palette), and
   inspect components (a diff viewer + an evidence panel that render
   public-safe by default), over a shared engine-free state model
   (`intui.kit.state`) with ready-made reductions, a command registry, a
   unified-diff parser, and a public-safety redactor.
4. **Examples** (`examples/`) — first-class runnable demos of every feature.

## Quickstart

```sh
uv sync
uv run python -m examples.operator_console  # the flagship: modes + whole kit
uv run python -m examples.mission_control   # the component kit demo
uv run python -m examples.hello_replay      # the foundation demo
uv run pytest                               # headless test suite
```

The **operator console** is the flagship — an agentic workbench with
Plan/Build/Inspect/Review modes and a conversation surface, composing every kit
component over one recorded run. See
[examples/operator_console/README.md](examples/operator_console/README.md).

See [examples/hello_replay/README.md](examples/hello_replay/README.md) and
the feature quickstart at
[specs/001-core-library-foundation/quickstart.md](specs/001-core-library-foundation/quickstart.md).

## Project governance

Spec-driven (GitHub Spec Kit): specs, plans, and tasks live under `specs/`;
principles live in [.specify/memory/constitution.md](.specify/memory/constitution.md).
