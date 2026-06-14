# Research & Decisions: Live Follow & Record

**Feature**: `016-follow-and-record` | **Date**: 2026-06-14

## D1 — Follow is a mode on `NdjsonStreamSource`, not a new source

**Decision**: Add `follow: bool = False` (+ `poll_interval: float = 0.25`) to
`NdjsonStreamSource`. With `follow=True` over a file path, after reaching EOF the
source keeps polling for appended lines instead of stopping.

**Why**: Follow shares everything with the file replayer (decode, unwrap,
malformed handling, `event_record_types`); a flag reuses it all and gives the
obvious API (`NdjsonStreamSource(path, follow=True)`, `--follow`). A separate
class would duplicate the source's structure.

**Alternatives rejected**: a standalone `FollowSource` — duplicates decode/unwrap;
an OS file-watch API (inotify/ReadDirectoryChangesW) — platform-specific and
heavier than a 0.25s poll for a line-append log.

## D2 — Tail via buffered `readline` polling (partial-line safe)

**Decision**: Open the file once; loop `readline()`; accumulate into a buffer
until a line ends with `\n`, then yield the complete line; when `readline()`
returns nothing, `await asyncio.sleep(poll_interval)` and retry.

**Why**: Text-mode `readline` resumes from the last position, so a line written in
pieces is reassembled and parsed exactly once (FR-002). Polling is simple,
cross-platform, and non-blocking via `asyncio.sleep`. The stream never ends at
EOF, so health stays LIVE — correct for a tail (the user quits with `q`).

**Alternatives rejected**: read-all-then-poll-size — re-reads/duplicates; seek/
tell arithmetic in text mode — fragile (opaque offsets).

## D3 — Follow stays live; cancels cleanly

**Decision**: The follow loop runs until the consuming worker is cancelled (app
quit). `Store.run` keeps the stream LIVE the whole time (no `mark_ended`).

**Why**: A tail has no natural end; LIVE health is the honest state. Textual
cancels the ingest worker on shutdown, which stops the async generator cleanly
(the `with open(...)` closes the handle).

**Alternatives rejected**: a sentinel to end follow — there isn't one for a tail;
the user ending the app is the end.

## D4 — Record = snapshot of accepted events via the existing writer

**Decision**: Add a read-only `Store.events` (delegating to
`EventStream.events`); the `ConsoleApp` record key writes those events to a
timestamped `.jsonl` with the existing `write_recording`.

**Why**: The stream already retains the accepted, ordered events; `write_recording`
already emits canonical ndjson. So record is a tiny composition — no new
serialization, and the output round-trips through `read_recording`/replay by
construction. Recording the *accepted* events means the file is always clean
(malformed input never lands in it).

**Alternatives rejected**: tee raw bytes from the source — would preserve wrapper
framing (needs an adapter to replay) and re-implement file writing; a continuous
live tee — more moving parts; a snapshot is enough for "save this run" and
pressing again captures more.

## D5 — Recorded output is canonical (no wrapper)

**Decision**: Because record dumps the store's parsed `Event`s, the file is
canonical bare envelopes regardless of the source (file, subprocess, IntentForge
adapter). It replays with plain `intui watch <file>` and no `--adapter`.

**Why**: The adapter/unwrap already happened on the way in; persisting the
canonical result is the most useful, replayable artifact (a portable fixture).

**Alternatives rejected**: persist the original wrapped/produced bytes — ties the
recording to the producer and an adapter for replay.

## D6 — Record key: `ctrl+s` on `ConsoleApp`; default timestamped path

**Decision**: Bind `ctrl+s` ("Save run") on `ConsoleApp`; it writes
`intui-recording-YYYYmmdd-HHMMSS.jsonl` in the working directory and notifies the
path. A write error is caught and shown via `notify`, not raised.

**Why**: `ctrl+s` reads as "save"; a timestamped default needs no prompt and
never overwrites. Showing the path closes the loop ("now `intui watch` it"). The
record action is footer-discoverable.

**Alternatives rejected**: a path prompt — extra UI for v1; overwriting a fixed
name — clobbers prior captures.

## Open questions / deferred

- **Wait-for-file** (follow a path that doesn't exist yet) — v1 requires it to
  exist; could poll for creation later.
- **Rotation/truncation** — best-effort append-only now.
- **Continuous tee-to-file** while recording — snapshot is v1; a live tee could
  come if asked.
- **Custom record path / `--record` CLI flag** — deferred; the key + default path
  covers the core need.
