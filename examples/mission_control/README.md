# mission_control

Demonstrates the task visualization kit (feature 002): a **task counter
chip**, a **two-level task tree**, and a **parallel lanes panel** — all
driven from one recorded run with two overlapping workers. The app defines
no custom reducers: it mounts the kit's ready-made `taskboard_slice()` and
binds the components to its selectors.

## Run it (fresh checkout)

```sh
uv sync
uv run python -m examples.mission_control
```

## What you'll see

- **Top bar — task counter chip**: `2 / 4 tasks complete`. Focus it and press
  `enter`/`space` (or click) to expand into a per-task list with status
  glyphs and a counts-by-status footer.
- **Left — task tree**: top-level tasks with status; arrow keys navigate,
  `enter` expands a task to reveal its work items (one task ends blocked, one
  work item failed, and a stray item lands under an `unassigned` bucket).
- **Right — workers**: one lane per worker with an animated Signal indicator
  (swoosh while active, steady once finished), its current activity, and last
  result. The two workers update independently as their events interleave.

## Keys

| Key | Action |
|-----|--------|
| `enter` / `space` | Expand/collapse the focused chip or tree node |
| arrows | Navigate the task tree |
| `tab` | Move focus between components |
| `q` | Quit |

## Why this example exists

Constitution Principle VIII: every shipped feature is demonstrated in a
runnable example. This one proves the kit components are data-driven,
keyboard-operable, and generic — a "lane" here is a worker, but the same
component shows CI jobs or batch runners unchanged.
