# Quickstart: Watch your pytest run

Turn a test run into a live console — no code.

## Record a run, then watch it

```sh
pip install intui
pytest --intui=run.jsonl        # run your suite as usual; emits a stream
intui watch run.jsonl           # tests as tasks/work items, failures, summary
```

## Watch it live (second terminal)

```sh
# terminal 1
pytest --intui=run.jsonl
# terminal 2
intui watch --follow run.jsonl  # new tests appear as they run
```

## What you see

- Each **module** is a task; each **test** a work item under it (press `t`).
- **Failures** show in the conversation, and the work item turns red.
- The **summary** (passed / failed / skipped / total + duration) shows as
  evidence (press `e`); the activity strip reflects pass/fail.
- It's an ordinary recording — **scrub** it (`space`, `,`/`.`), or save a copy
  (`ctrl+s`).

## Notes

- The plugin ships with intui and is **inert unless you pass `--intui`** — it
  won't touch your normal pytest runs.
- The stream is **canonical** — no adapter needed; `pytest` is just another
  producer of the in-TUI-tion event contract.
- v1 measures a single (non-`-n`/xdist) process; failure detail is a concise
  message (not a full traceback dump).
