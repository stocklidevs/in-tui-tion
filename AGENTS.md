<!-- SPECKIT START -->
For additional context about technologies to be used, project structure,
shell commands, and other important information, read the current plan:
`specs/001-core-library-foundation/plan.md`

Key facts: Python 3.11–3.13 library (`src/intui/`, hatchling + uv, pytest);
built on Textual 6.x, but the pipeline core (`intui.events/state/viewmodels/
actions/theming`) imports no Textual — only `intui.widgets` and `intui.app`
do. Governance: `.specify/memory/constitution.md` (v2.0.0).
<!-- SPECKIT END -->
