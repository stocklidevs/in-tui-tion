# hello_replay

The foundation example: a state-driven TUI that replays a recorded run
(`recording.jsonl`) through the in-TUI-tion pipeline — events → reducers →
snapshots → view models → widgets. Nothing on screen is drawn imperatively;
everything derives from the event stream.

## Run it (fresh checkout)

Requires [uv](https://docs.astral.sh/uv/) (it installs Python itself if
needed) and a modern terminal (Windows Terminal, macOS Terminal/iTerm2, or a
common Linux/WSL terminal).

```sh
git clone <repo-url> in-tui-tion
cd in-tui-tion
uv sync
uv run python -m examples.hello_replay
```

## What you'll see

- A **Signal** indicator in the top bar: KITT-style swoosh while the run is
  working, steady green check when it passes, red strobe on failure — color,
  motion, glyph, and label all derive from the replayed run's status.
- A **status line** with run status and stream health (watch it report
  "stream ended" when the recording finishes).
- A **scrolling event log** reduced from the replayed events.

## Keys

| Key | Action |
|-----|--------|
| `r` | Re-run the replay (appends the recording again as new events) |
| `x` | Clear the log — **risky**, so it asks for confirmation (`y`/`n`) |
| `t` | Switch theme (dark ⇄ light) — no widget code involved |
| `q` | Quit |

Everything is keyboard-operable; the footer shows available keys at all
times.

## Why this example exists

Constitution Principle VIII: every shipped library feature must be
demonstrated in a runnable example. This one covers the event pipeline,
recording replay, view-model-bound widgets, intent-based input with risky
confirmation, theming, and the Signal primitive.
