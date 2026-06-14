"""emit_demo: a tiny producer built entirely with the Producer SDK (feature 012).

Run it two ways:

    # watch it live (the SDK emits to stdout; the runner spawns this script):
    intui watch -- python -m examples.emit_demo

    # or capture to a file and replay:
    python -m examples.emit_demo > run.ndjson && intui watch run.ndjson

No JSON is written by hand — every line is a `run_recorder` call.
"""

from __future__ import annotations

from intui import run_recorder

_BEFORE = "def add(a, b):\n    return a + b\n"
_AFTER = "def add(a, b):\n    return a + b  # sum\n\n\ndef sub(a, b):\n    return a - b\n"
_README_BEFORE = "# calc\n"
_README_AFTER = "# calc\n\nA tiny calculator with add and sub.\n"


def main() -> None:
    rec = run_recorder()  # default sink = stdout (live-watchable)
    with rec.run(summary="Build the calculator"):
        rec.agent("Planning the build…")
        with rec.task("build", "Build the app") as build:
            with build.work_item("scaffold", "scaffold files"):
                rec.file_written("README.md", change_type="added")
                rec.diff("README.md", before=_README_BEFORE, after=_README_AFTER)
            with build.work_item("implement", "implement calc"):
                rec.file_written("src/calc.py", change_type="added")
                rec.file_written("src/__init__.py", change_type="added")
                rec.diff("src/calc.py", before=_BEFORE, after=_AFTER)
        with rec.task("verify", "Verify") as verify, verify.work_item("tests", "run tests"):
            rec.agent("All tests passed.")
        rec.evidence(pass_rate="100%", tests="6 passed", certified="gold")


if __name__ == "__main__":
    main()
