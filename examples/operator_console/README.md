# operator_console

The flagship example: an agentic **operator console** composing the whole
in-TUI-tion kit — conversation, task chip, task tree, parallel lanes, activity
signal, command surfaces, diff viewer, evidence panel — organized around four
**modes** (Plan, Build, Inspect, Review) and driven by one recorded run.

It demonstrates the full contract end to end: switching modes flows as an
intent → `mode_changed` event → reduced state → UI, the same loop as every
other interaction. A full-width **activity strip** (the signature KITT swoosh)
sweeps across the top in the run's state color, and a **prompt** at the bottom
lets you type a goal and submit it.

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

## Type a prompt

The prompt field at the bottom is live: type a goal and press Enter. Your text
appears in the conversation as a user message, the activity strip flashes
`thinking`, and a scripted acknowledgement follows. (There is no live agent yet
— only the reply is simulated; the input → intent → message → reply loop is
real and will drive a real backend once the IntentForge adapter lands.)

## Activity strip (the KITT swoosh)

The full-width strip across the top is the signature ambient signal (R6). Its
colour and motion are data-driven from the run's overall state — a red swoosh
while working, cyan while verifying, steady green when passed, a fast red strobe
on failure — always with a textual label so state is readable without colour.

## Keys

| Key | Action |
|-----|--------|
| `1`–`4` | Switch mode |
| type + `enter` | Submit a prompt (focus the bottom field) |
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
