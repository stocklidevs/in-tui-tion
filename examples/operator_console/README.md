# operator_console

The flagship example: an agentic **operator console** composing the whole
in-TUI-tion kit — conversation, task chip, task tree, parallel lanes, activity
signal, command surfaces, diff viewer, evidence panel — organized around four
**modes** (Plan, Build, Inspect, Review) and driven by one recorded run.

It demonstrates the full contract end to end: switching modes flows as an
intent → `mode_changed` event → reduced state → UI, the same loop as every
other interaction.

## Run it (fresh checkout)

```sh
uv sync
uv run python -m examples.operator_console
```

## Modes

| Key | Mode | Shows |
|-----|------|-------|
| `1` | Plan | the conversation + the plan's task counter |
| `2` | Build | activity signal, task chip, task tree, parallel worker lanes |
| `3` | Inspect | diff viewer + evidence panel (public-safe) |
| `4` | Review | the run's evidence summary |

The conversation transcript (agent/user/system messages, a clarifying
question, an approval prompt) is persistent on the left across all modes. The
replay also drives modes on its own, so the console walks Plan → Build →
Inspect → Review as the run progresses; you can switch at any time.

## Keys

| Key | Action |
|-----|--------|
| `1`–`4` | Switch mode |
| arrows / `enter` | Navigate the task tree / diff file list; expand nodes |
| `a` `d` `e` | Commands: approve / diff / evidence |
| `x` | Cancel run (risky — confirms first) |
| `ctrl+p` / `p` | Open the command palette |
| `q` | Quit |

## Public-safe by default

Inspect and Review render evidence and diffs **public-safe**: the absolute
config path in the diff and the operator workdir in evidence are replaced with
a `‹redacted›` marker (Constitution Principle VI).

## Why this example exists

This is the demanding seed the whole library was built for (Principle VIII):
proof that the generic kit composes into a real operator workbench, every pane
driven by reduced event state rather than mock widgets.
