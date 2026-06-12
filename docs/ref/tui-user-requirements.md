# Generic Agentic TUI User Requirements

## Purpose

Define user-facing requirements for a generic Python TUI framework for agentic
applications, using IntentForge as the first demanding seed application.

The intended product is not a plain log viewer. It is an operator workbench where
a user can prompt for an application, review the generated plan, steer execution,
watch live work, inspect diffs and artifacts, approve or interrupt actions, and
review evidence after completion.

This document is written to be handed to a future Codex session as starting
context for design or implementation.

## Inspiration

- Grok Build interactive TUI: rich fullscreen, mouse-interactive coding agent
  experience, visible plan mode, slash commands, session controls, and
  streaming JSON headless output.
- IntentForge current product shape: deterministic harness, public-safe run
  traces, plans, work items, Patch VM transactions, verification gates,
  evidence notes, ACB scores, and repeatability summaries.
- Local mockup: `.superpowers/brainstorm/kitt-if-tui-concept.html`

Useful references:

- https://docs.x.ai/build/overview
- https://docs.x.ai/build/modes-and-commands
- https://docs.x.ai/build/cli/headless-scripting
- `specs/304-application-assembly-milestone/plan.md`
- `docs/assessment.md`

## Product Vision

The TUI should feel like a live command center for agentic work.

Primary loop:

```text
prompt goal
  -> agent asks clarifying questions
  -> agent proposes spec, milestones, tasks, and plan
  -> user approves or steers
  -> work starts
  -> TUI shows live tasks, subagents, diffs, files, gates, and evidence
  -> user can interrupt, cancel, approve, retry, rework, compare, or inspect
  -> final evidence and run history remain explorable
```

## Design Principles

1. The TUI renders structured state, not raw logs.
2. The TUI should be generic, with app-specific adapters underneath.
3. The TUI should support both live execution and historical evidence review.
4. High-level user-facing tasks should stay visible, with drilldown into lower
   level execution details.
5. The TUI should be keyboard-first and mouse-friendly.
6. Visual effects must communicate state. Eye candy is welcome when it carries
   meaning.
7. Mutating actions should route through the host application's action API or
   adapter, not through ad hoc file or process manipulation.
8. IntentForge-specific constraints, especially public-safe evidence and
   deterministic execution boundaries, should be preserved.

## Personas

### Operator

Prompts for a software goal, answers clarification questions, approves plans,
monitors progress, inspects diffs, and decides whether to retry, rework, or stop.

### Reviewer

Opens completed runs, inspects evidence, compares results, reviews diffs and
artifacts, and determines whether the run is trustworthy.

### Framework Integrator

Adapts another Python application to the TUI by mapping its events, state,
artifacts, and actions into the common TUI contract.

## Core Requirements

### R1: Prompt And Conversation Surface

The TUI MUST provide a persistent prompt surface for natural-language
interaction with the active agent or application.

The conversation surface MUST support:

- agent messages
- user messages
- system/status messages
- clarifying questions
- approval prompts
- side questions that do not interrupt the current run

### R2: Visible Plan Mode

The TUI MUST support a plan-first mode.

Plan mode SHOULD:

- show the current plan persistently
- display specs, milestones, and tasks before execution
- allow the agent to ask clarifying questions
- block or discourage uncontrolled writes until the plan is approved
- expose an approval action

### R3: Task Counter Chip

The TUI MUST show a compact task counter such as:

```text
7 / 14 tasks complete
```

The task counter MUST be expandable into a task list.

The expanded task list MUST show:

- checked completed tasks
- active tasks
- blocked or waiting tasks
- queued tasks
- task counts by status when available

### R4: Two-Level Task Model

The TUI MUST support both user-facing plan tasks and lower-level execution work.

Recommended model:

```text
user-facing task
  -> work item
    -> subagent lane
    -> tool call
    -> diff
    -> verification gate
    -> evidence row
```

For IntentForge, the top level should be spec/milestone/task oriented. Drilldown
should reveal blueprint lowering, Intent Tree items, Patch VM transactions,
verification gates, generated files, diffs, and evidence.

### R5: Parallel Lanes And Subagents

The TUI MUST represent parallel work.

When multiple subagents or workers are active, the TUI SHOULD show each as a
lane under the parent task.

Each lane SHOULD show:

- name or role
- current activity
- status
- activity indicator
- last event or result

### R6: Activity Signals

The TUI MUST provide a compact ambient activity indicator. The KITT-inspired
swooshing light is the preferred visual metaphor.

The activity indicator MUST change color based on state:

- red: planning, reasoning, or model thinking
- amber: waiting for approval, clarification, or user input
- cyan: verification, tests, or checks running
- green: passed, committed, or completed
- violet: comparing runs, replaying history, or browsing archived evidence
- fast red strobe: failed gate, blocked task, or urgent intervention

The color must be data-driven, not hard-coded decoration.

### R7: Bottom Command Menu

The TUI MUST provide a bottom command menu with always-visible actions.

Initial actions SHOULD include:

- Interrupt
- Cancel
- Approve
- Tasks
- Diff
- Files
- Evidence
- Compare
- Graph
- Help

Actions that mutate execution state MUST be confirmable when risky.

### R8: Diff And Artifact Inspection

The TUI MUST support diff inspection.

For IntentForge, this SHOULD include:

- green/red code diffs
- changed file list
- generated file browser
- plan/spec/evidence artifact viewer
- link from task/work item to its produced artifacts

Initial file exploration SHOULD be read-oriented. Direct file editing can be a
later capability and should route through an explicit action or patch proposal.

### R9: Evidence Explorer

The TUI MUST support evidence browsing for completed and live runs.

For IntentForge, evidence views SHOULD include:

- pass rate
- export coverage
- quality issue count
- generated-code inspection status and score
- ACB score and level
- operation counts
- drift
- failure categories
- evidence signature
- delivered files
- run history

### R10: Comparison View

The TUI SHOULD support comparing runs.

Comparison SHOULD include:

- pass/fail status
- evidence signatures
- operation counts
- drift
- quality scores
- delivered files
- failure categories
- timing or duration when available

### R11: Graph Views

The TUI SHOULD support graph-like views when they clarify structure.

Useful graph views:

- plan dependency graph
- task/work-item tree
- subagent lane timeline
- verification gate timeline
- failure taxonomy
- run comparison chart

Graphs should be navigable and collapsible. They should supplement, not replace,
task lists and tables.

### R12: Session Browser

The TUI SHOULD support browsing, resuming, and comparing previous sessions or
runs.

Session browsing SHOULD expose:

- session title or goal
- status
- last update
- model/provider label when public-safe
- evidence availability
- artifacts

### R13: Modes

The TUI SHOULD support explicit modes.

Initial modes:

- Plan: clarify, spec, milestones, tasks, approval
- Build: execute work, show active tasks, lanes, tools, diffs
- Inspect: browse files, artifacts, evidence, graphs
- Review: compare output to plan, inspect final evidence, request rework

Modes can be switched through keyboard shortcuts, command palette, or slash
commands.

## Data Interaction Model

The TUI should be built around a common internal contract:

```text
app adapter
  -> append-only event stream
  -> reducer/state store
  -> view models
  -> widgets
  -> user actions
  -> app adapter
```

### Event Stream

Events are append-only facts emitted by the app or translated by an adapter.

Suggested envelope:

```json
{
  "version": "1",
  "event_id": "evt-001",
  "run_id": "run-123",
  "timestamp": "2026-06-12T12:00:00Z",
  "type": "task_started",
  "scope": {
    "session_id": "session-abc",
    "task_id": "task-plan",
    "work_item_id": "work-api",
    "lane_id": "subagent-a"
  },
  "status": "running",
  "summary": "Checking API shape",
  "payload": {}
}
```

Common event types:

- `session_started`
- `mode_changed`
- `message_added`
- `question_requested`
- `approval_requested`
- `approval_resolved`
- `task_created`
- `task_started`
- `task_completed`
- `task_blocked`
- `work_item_started`
- `work_item_completed`
- `subagent_started`
- `subagent_activity`
- `subagent_completed`
- `tool_call_started`
- `tool_call_completed`
- `diff_ready`
- `artifact_ready`
- `gate_started`
- `gate_passed`
- `gate_failed`
- `evidence_ready`
- `comparison_ready`
- `run_completed`
- `run_failed`
- `run_interrupted`
- `run_cancelled`

### Derived State

The TUI should reduce events into a current state snapshot.

Derived state SHOULD include:

- current mode
- active signal color/state
- task counts
- expanded/collapsed task tree
- active tasks and lanes
- blocked approvals
- active diff/artifact
- evidence summary
- available actions
- connection/stream health

### Artifacts

Artifacts are external or in-memory resources linked from state.

Artifact types:

- plan
- spec
- task list
- diff
- file
- directory
- test result
- verification output
- evidence note
- summary JSON
- graph model
- comparison report

Artifacts SHOULD have stable IDs and metadata:

```json
{
  "artifact_id": "artifact-diff-001",
  "type": "diff",
  "title": "API route changes",
  "path": "src/support/api.py",
  "producer": "work-api",
  "public_safe": true
}
```

### Actions

The TUI should emit intentful actions back to the host app or adapter.

Initial actions:

- `approve`
- `reject`
- `answer_question`
- `interrupt`
- `cancel`
- `retry`
- `request_rework`
- `open_artifact`
- `compare_runs`
- `switch_mode`
- `toggle_task`
- `focus_lane`

Actions SHOULD be validated by the adapter before execution.

Risky actions SHOULD require confirmation.

## IntentForge Adapter Requirements

The first adapter SHOULD consume existing IntentForge structures without forcing
the core harness to become a TUI runtime.

Initial IF input sources:

- CLI `--json` final payloads
- CLI `--progress` newline-delimited JSON progress events
- `RunTrace` summaries
- project/session matrix summaries
- assembly benchmark summaries
- evidence notes
- generated-code inspection summaries
- ACB score payloads
- workspace file manifests and diffs

The IF adapter SHOULD translate these into the common event/state/artifact/action
contract.

Future IF work can emit richer events directly, but adapter-first is preferred
for the initial generic framework.

## Non-Functional Requirements

### Responsiveness

The TUI SHOULD remain responsive while long-running work streams events.

### Accessibility

The TUI SHOULD support keyboard navigation for all primary actions. Color should
not be the only status signal.

### Public Safety

For IF, the TUI MUST respect public-safe evidence boundaries. Provider endpoints,
tokens, local absolute paths, raw provider configuration, and unsafe local
details must not appear in public evidence views.

### Portability

The framework SHOULD run on common modern terminals on Windows, macOS, Linux,
and WSL.

### Extensibility

The TUI SHOULD be generic enough for non-IF applications. App-specific knowledge
should live in adapters, schemas, and view model mappers.

## Initial MVP Proposal

MVP goal:

Build a read-mostly TUI prototype that can show one live or replayed IF run with
task counts, expanded tasks, lanes, diffs, evidence summary, and bottom actions.

MVP scope:

- static or replayed event stream
- task counter chip
- collapsible task tree
- activity signal strip
- parallel lane display
- conversation/prompt surface
- diff viewer
- evidence summary panel
- bottom command menu
- adapter for one IF summary/run-trace shape

MVP can defer:

- real process control
- direct file editing
- remote sync
- plugin marketplace
- full session browser
- advanced graph layout

## Open Questions

1. Should the first implementation use Textual, prompt_toolkit, Rich Live, or a
   custom terminal rendering layer?
2. Should live execution be launched by the TUI, attached to an existing process,
   or both?
3. Should the common event schema be formally versioned from day one?
4. Which graph view is most valuable first: task dependency, timeline, or run
   comparison?
5. Should direct file manipulation ever be allowed, or should all edits become
   proposed actions/rework requests?
6. How should approvals behave in headless or CI-style runs?
7. How much of the Grok-like slash command model should be core versus adapter
   provided?

