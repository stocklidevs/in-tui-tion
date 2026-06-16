# pytest_console

Watch a **pytest** run as an in-TUI-tion console — feature 019. The plugin ships
with intui and is inert unless you pass `--intui`.

## Run it

```sh
pip install intui
pytest examples/pytest_console --intui=run.jsonl
intui watch run.jsonl
```

Or live, in a second terminal:

```sh
# terminal 1
pytest examples/pytest_console --intui=run.jsonl
# terminal 2
intui watch --follow run.jsonl
```

## What you see

The sample suite has a pass, another pass, an intentional failure, and a skip, so
the console shows every state:

- press `t` — each **module** is a task, each **test** a work item (the failure
  is red);
- press `e` — the **summary** as evidence (passed/failed/skipped/total/duration);
- the **activity strip** turns to failure because a test failed;
- it's an ordinary recording — **scrub** it (`space`, `,`/`.`) or save a copy
  (`ctrl+s`).

The stream is canonical — `pytest` is just another producer of the in-TUI-tion
event contract, so no adapter is needed.
