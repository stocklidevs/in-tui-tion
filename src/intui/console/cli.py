"""`intui watch` — render a console from a stream file or a spawned producer.

    intui watch [--public-safe | --no-public-safe] [--rate R] <file.jsonl>
    intui watch [--public-safe | --no-public-safe] -- <command> [args...]

A missing file or a command that cannot start yields a clear ``error: ...`` on
stderr and a non-zero exit — never a traceback.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

from intui.adapters import IntentForgeSource
from intui.console.app import build_console
from intui.events import EventSource, NdjsonStreamSource, SubprocessSource

#: Record types unwrapped by default (matches real producer output).
DEFAULT_RECORD_TYPES = ("run_trace_event",)


def _fail(message: str) -> int:
    print(f"error: {message}", file=sys.stderr)
    return 1


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="intui watch",
        description="Render a console from a canonical event stream.",
    )
    parser.add_argument(
        "--public-safe",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="redact diffs/evidence (default: on; --no-public-safe to disable)",
    )
    parser.add_argument(
        "--rate", type=float, default=None, help="replay rate in events/second (file form)"
    )
    parser.add_argument(
        "--adapter",
        choices=("none", "intentforge"),
        default="none",
        help="normalize a producer's stream (default: none = canonical vocabulary)",
    )
    parser.add_argument(
        "--metrics",
        action="store_true",
        help="watch a command's resources (CPU/memory) instead of its stdout "
        "(use with `-- <command>`; needs in-tui-tion[metrics])",
    )
    parser.add_argument(
        "--follow",
        action="store_true",
        help="tail a growing stream file (keep reading appended lines)",
    )
    parser.add_argument(
        "target",
        nargs="?",
        help="a .jsonl stream file (or use `-- <command>` to spawn a producer)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    usage = (
        "usage: intui watch [--adapter {none,intentforge}] "
        "[--public-safe|--no-public-safe] [--rate R] (<file.jsonl> | -- <command>)"
    )
    if argv and argv[0] in ("-h", "--help", "help"):
        print(usage)
        return 0
    if not argv or argv[0] != "watch":
        print(usage, file=sys.stderr)
        return 2
    rest = argv[1:]

    cmd: list[str] | None = None
    if "--" in rest:
        sep = rest.index("--")
        opt_tokens, cmd = rest[:sep], rest[sep + 1 :]
    else:
        opt_tokens = rest

    parser = _build_parser()
    try:
        ns = parser.parse_args(opt_tokens)
    except SystemExit as exc:  # argparse already printed a message
        return int(exc.code or 2)

    intentforge = ns.adapter == "intentforge"
    source: EventSource
    if cmd is not None:
        if ns.follow:
            return _fail(
                "--follow is for a stream file, not a command (a command is already live)"
            )
        if not cmd:
            return _fail("no command given after `--`")
        if shutil.which(cmd[0]) is None and not Path(cmd[0]).is_file():
            return _fail(f"command not found: {cmd[0]}")
        if ns.metrics:
            from intui.events import ProcessMonitorSource

            source = ProcessMonitorSource(cmd)
        elif intentforge:
            source = IntentForgeSource.from_command(cmd)
        else:
            source = SubprocessSource(cmd, event_record_types=DEFAULT_RECORD_TYPES)
    else:
        if ns.metrics:
            return _fail("--metrics needs a command: intui watch --metrics -- <command>")
        if ns.target is None:
            return _fail("no stream file or `-- <command>` given")
        path = Path(ns.target)
        if not path.is_file():
            return _fail(f"file not found: {ns.target}")
        source = (
            IntentForgeSource(path)
            if intentforge
            else NdjsonStreamSource(
                path, event_record_types=DEFAULT_RECORD_TYPES, rate=ns.rate, follow=ns.follow
            )
        )

    app = build_console(source, public_safe=ns.public_safe)
    app.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
